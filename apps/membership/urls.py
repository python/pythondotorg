"""URL configuration for the membership app."""

from django.urls import path

from apps.membership import views

urlpatterns = [
    path("", views.Membership.as_view(), name="membership"),
]
