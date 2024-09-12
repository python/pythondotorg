from django.urls import path

from . import views


urlpatterns = [
    path('application/new/', views.NewSponsorshipApplicationView.as_view(),
        name="new_sponsorship_application",
    ),
    path('application/', views.SelectSponsorshipApplicationBenefitsView.as_view(),
        name="select_sponsorship_application_benefits",
    ),
]
