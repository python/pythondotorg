import json
from itertools import chain
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.utils import ErrorList
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView, FormView, DetailView

from .models import (
    Sponsor,
    SponsorshipBenefit,
    SponsorshipPackage,
    SponsorshipProgram,
    Sponsorship,
)

from sponsors import cookies
from sponsors import use_cases
from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm


class SelectSponsorshipApplicationBenefitsView(FormView):
    form_class = SponsorshiptBenefitsForm
    template_name = "sponsors/sponsorship_benefits_form.html"

    def get_context_data(self, *args, **kwargs):
        programs = SponsorshipProgram.objects.all()
        packages = SponsorshipPackage.objects.all()
        benefits_qs = SponsorshipBenefit.objects.select_related("program")
        capacities_met = any(
            [
                any([not b.has_capacity for b in benefits_qs.filter(program=p)])
                for p in programs
            ]
        )
        kwargs.update(
            {
                "benefit_model": SponsorshipBenefit,
                "sponsorship_packages": packages,
                "capacities_met": capacities_met,
            }
        )
        return super().get_context_data(*args, **kwargs)

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy("new_sponsorship_application")
        else:
            return f"{settings.LOGIN_URL}?next={reverse('new_sponsorship_application')}"

    def get_initial(self):
        return cookies.get_sponsorship_selected_benefits(self.request)

    def form_valid(self, form):
        if not self.request.session.test_cookie_worked():
            error = ErrorList()
            error.append("You must allow cookies from python.org to proceed.")
            form._errors.setdefault("__all__", error)
            return self.form_invalid(form)

        response = super().form_valid(form)
        self._set_form_data_cookie(form, response)
        return response

    def get(self, request, *args, **kwargs):
        request.session.set_test_cookie()
        return super().get(request, *args, **kwargs)

    def _set_form_data_cookie(self, form, response):
        data = {
            "package": "" if not form.get_package() else form.get_package().id,
        }
        for fname, benefits in [
            (f, v)
            for f, v in form.cleaned_data.items()
            if f.startswith("benefits_") or f == 'add_ons_benefits'
        ]:
            data[fname] = sorted(b.id for b in benefits)

        cookies.set_sponsorship_selected_benefits(response, data)


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class NewSponsorshipApplicationView(FormView):
    form_class = SponsorshipApplicationForm
    template_name = "sponsors/new_sponsorship_application_form.html"

    def _redirect_back_to_benefits(self):
        msg = "You have to select sponsorship package and benefits before."
        messages.add_message(self.request, messages.INFO, msg)
        return redirect(reverse("select_sponsorship_application_benefits"))

    @property
    def benefits_data(self):
        return cookies.get_sponsorship_selected_benefits(self.request)

    def get(self, *args, **kwargs):
        if not self.benefits_data:
            return self._redirect_back_to_benefits()
        return super().get(*args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_context_data(self, *args, **kwargs):
        package_id = self.benefits_data.get("package")
        package = (
            None if not package_id else SponsorshipPackage.objects.get(id=package_id)
        )
        benefits_ids = chain(
            *(self.benefits_data[k] for k in self.benefits_data if k != "package")
        )
        benefits = SponsorshipBenefit.objects.filter(id__in=benefits_ids)

        # sponsorship benefits holds selected package's benefits
        # added benefits holds holds extra benefits added by users
        added_benefits, sponsorship_benefits = [], benefits
        price = None
        if package and not package.has_user_customization(benefits):
            price = package.sponsorship_amount
        elif package:
            sponsorship_benefits = []
            package_benefits = package.benefits.all()
            for benefit in benefits:
                if benefit in package_benefits:
                    sponsorship_benefits.append(benefit)
                else:
                    added_benefits.append(benefit)
        else:
            added_benefits, sponsorship_benefits = sponsorship_benefits, []

        kwargs.update(
            {
                "sponsorship_package": package,
                "sponsorship_benefits": sponsorship_benefits,
                "added_benefits": added_benefits,
                "sponsorship_price": price,
            }
        )
        return super().get_context_data(*args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        benefits_form = SponsorshiptBenefitsForm(data=self.benefits_data)
        if not benefits_form.is_valid():
            return self._redirect_back_to_benefits()

        sponsor = form.save()

        uc = use_cases.CreateSponsorshipApplicationUseCase.build()
        sponsorship = uc.execute(
            self.request.user,
            sponsor,
            benefits_form.get_benefits(),
            benefits_form.get_package(),
            request=self.request,
        )
        notified = uc.notifications[1].get_recipient_list(
            {"user": self.request.user, "sponsorship": sponsorship}
        )

        response = render(
            self.request,
            "sponsors/sponsorship_application_finished.html",
            context={"sponsorship": sponsorship, "notified": notified},
        )
        cookies.delete_sponsorship_selected_benefits(response)
        return response


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class SponsorshipDetailView(DetailView):
    context_object_name = 'sponsorship'
    template_name = 'sponsors/sponsorship_detail.html'

    def get_queryset(self):
        return self.request.user.sponsorships
