"""URL configuration for the blogs app."""

from django.urls import path

from apps.blogs import views

urlpatterns = [
    path("", views.BlogHome.as_view(), name="blog"),
]
