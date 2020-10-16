from django.conf.urls import url

from . import views


urlpatterns = [
    url(r"^$", views.SponsorList.as_view(), name="sponsor_list"),
    url(
        r"^application/$",
        views.NewSponsorshipApplication.as_view(),
        name="new_sponsorship_application",
    ),
]
