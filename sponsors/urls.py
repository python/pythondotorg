from django.conf.urls import url
from django.views.generic.base import TemplateView

from . import views


urlpatterns = [
    url(
        r"^application/new/$",
        views.NewSponsorshipApplicationView.as_view(),
        name="new_sponsorship_application",
    ),
    url(
        r"^application/$",
        views.SelectSponsorshipApplicationBenefitsView.as_view(),
        name="select_sponsorship_application_benefits",
    ),
]
