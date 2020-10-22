from django.http import JsonResponse
from django.views.generic import ListView, FormView
from django.urls import reverse_lazy

from .models import Sponsor, SponsorshipBenefit, SponsorshipPackage

from sponsors.forms import SponsorshiptBenefitsForm


class SponsorList(ListView):
    model = Sponsor
    template_name = "sponsors/sponsor_list.html"
    context_object_name = "sponsors"

    def get_queryset(self):
        return Sponsor.objects.select_related().published()


class NewSponsorshipApplication(FormView):
    form_class = SponsorshiptBenefitsForm
    template_name = "sponsors/sponsorship_benefits_form.html"
    success_url = reverse_lazy("new_sponsorship_application")

    def get_context_data(self, *args, **kwargs):
        kwargs.update(
            {
                "benefit_model": SponsorshipBenefit,
                "sponsorship_packages": SponsorshipPackage.objects.all(),
            }
        )
        return super().get_context_data(*args, **kwargs)
