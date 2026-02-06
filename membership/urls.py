from django.urls import path

from . import views

urlpatterns = [
    path("", views.Membership.as_view(), name="membership"),
]
