from django.urls import path

from . import views

urlpatterns = [
    path("", views.BlogHome.as_view(), name="blog"),
]
