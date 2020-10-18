from django.http import JsonResponse
from django.views.generic import ListView, FormView
from django.urls import reverse_lazy

from .models import Sponsor

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


def price_calculator_view(request):
    form = SponsorshiptBenefitsForm(data=request.GET)
    if form.is_valid():
        status_code = 200
        data = {"cost": sum(b.internal_value for b in form.get_benefits())}
    else:
        status_code = 400
        data = {"errors": form.errors}

    return JsonResponse(data, status=status_code)
