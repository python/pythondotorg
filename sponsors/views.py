import json
from itertools import chain
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.generic import ListView, FormView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect

from .models import Sponsor, SponsorshipBenefit, SponsorshipPackage, Sponsorship

from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm
from sponsors import cookies


@method_decorator(staff_member_required(login_url=settings.LOGIN_URL), name="dispatch")
class SelectSponsorshipApplicationBenefitsView(FormView):
    form_class = SponsorshiptBenefitsForm
    template_name = "sponsors/sponsorship_benefits_form.html"

    def get_context_data(self, *args, **kwargs):
        kwargs.update(
            {
                "benefit_model": SponsorshipBenefit,
                "sponsorship_packages": SponsorshipPackage.objects.all(),
            }
        )
        return super().get_context_data(*args, **kwargs)

    def get_success_url(self):
        if self.request.user.is_authenticated:
            return reverse_lazy("new_sponsorship_application")
        else:
            # TODO unit test this scenario after removing staff_member_required decortor
            return settings.LOGIN_URL

    def get_initial(self):
        return cookies.get_sponsorship_selected_benefits(self.request)

    def form_valid(self, form):
        response = super().form_valid(form)
        self._set_form_data_cookie(form, response)
        return response

    def _set_form_data_cookie(self, form, response):
        # TODO: make sure user accepts cookies with set_test_cookie
        data = {
            "package": "" if not form.get_package() else form.get_package().id,
        }
        for fname, benefits in [
            (f, v) for f, v in form.cleaned_data.items() if f.startswith("benefits_")
        ]:
            data[fname] = sorted([b.id for b in benefits])

        cookies.set_sponsorship_selected_benefits(response, data)


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class NewSponsorshipApplicationView(FormView):
    form_class = SponsorshipApplicationForm
    template_name = "sponsors/new_sponsorship_application_form.html"
    success_url = reverse_lazy("finish_sponsorship_application")

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
            *[self.benefits_data[k] for k in self.benefits_data if k != "package"]
        )
        kwargs.update(
            {
                "sponsorship_package": package,
                "sponsorship_benefits": SponsorshipBenefit.objects.filter(
                    id__in=benefits_ids
                ),
            }
        )
        return super().get_context_data(*args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        benefits_form = SponsorshiptBenefitsForm(data=self.benefits_data)
        if not benefits_form.is_valid():
            return self._redirect_back_to_benefits()

        sponsor = form.save()
        Sponsorship.new(
            sponsor, benefits_form.get_benefits(), benefits_form.get_package()
        )

        response = super().form_valid(form)
        cookies.delete_sponsorship_selected_benefits(response)
        return response
