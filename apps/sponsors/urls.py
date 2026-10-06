"""URL configuration for the sponsors app."""

from django.urls import include, path

from apps.sponsors import views

urlpatterns = [
    path(
        "application/new/",
        views.NewSponsorshipApplicationView.as_view(),
        name="new_sponsorship_application",
    ),
    path(
        "application/",
        views.SelectSponsorshipApplicationBenefitsView.as_view(),
        name="select_sponsorship_application_benefits",
    ),
    path(
        "documents/<path:name>/",
        views.download_contract_document,
        name="download_contract_document",
    ),
    # Staff-only management UI
    path("manage/", include("apps.sponsors.manage.urls")),
]
