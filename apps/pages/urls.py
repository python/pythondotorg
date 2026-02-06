"""URL configuration for the pages app."""

from django.urls import path

from apps.pages.views import PageView

urlpatterns = [
    path("<path:path>/", PageView.as_view(), name="page_detail"),
]
