"""URL configuration for the boxes app."""

from django.urls import path

from apps.boxes.views import box

urlpatterns = [
    path("<slug:label>/", box, name="box"),
]
