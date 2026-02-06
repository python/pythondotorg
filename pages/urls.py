from django.urls import path

from .views import PageView

urlpatterns = [
    path("<path:path>/", PageView.as_view(), name="page_detail"),
]
