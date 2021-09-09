from . import views
from django.urls import path

urlpatterns = [
    path('', views.BlogHome.as_view(), name='blog'),
]
