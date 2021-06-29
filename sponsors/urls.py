from django.conf.urls import url
from django.urls import path

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
    path(
        "application/<int:pk>/detail/",
        views.SponsorshipDetailView.as_view(),
        name="sponsorship_application_detail",
    ),
]
