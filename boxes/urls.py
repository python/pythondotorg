from django.urls import path

from .views import box

urlpatterns = [
    path("<slug:label>/", box, name="box"),
]
