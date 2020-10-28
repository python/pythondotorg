from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.views.generic import ListView, FormView
from django.urls import reverse_lazy

from .models import Sponsor, SponsorshipBenefit, SponsorshipPackage

from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm


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
    success_url = reverse_lazy("select_sponsorship_application_benefits")

    def get_context_data(self, *args, **kwargs):
        kwargs.update(
            {
                "benefit_model": SponsorshipBenefit,
                "sponsorship_packages": SponsorshipPackage.objects.all(),
            }
        )
        return super().get_context_data(*args, **kwargs)


@method_decorator(login_required(login_url=settings.LOGIN_URL), name="dispatch")
class NewSponsorshipApplicationView(FormView):
    form_class = SponsorshipApplicationForm
    template_name = "sponsors/new_sponsorship_application_form.html"
    success_url = reverse_lazy("new_sponsorship_application")
