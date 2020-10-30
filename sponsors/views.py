import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.generic import ListView, FormView
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect

from .models import Sponsor, SponsorshipBenefit, SponsorshipPackage

from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm
from sponsors import cookies


class SponsorList(ListView):
    model = Sponsor
    template_name = "sponsors/sponsor_list.html"
    context_object_name = "sponsors"

    def get_queryset(self):
        return Sponsor.objects.select_related().published()


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

    def get(self, *args, **kwargs):
        if not cookies.get_sponsorship_selected_benefits(self.request):
            return redirect(reverse("select_sponsorship_application_benefits"))
        return super().get(*args, **kwargs)

    def form_invalid(self, *args, **kwargs):
        return super().form_invalid(*args, **kwargs)
