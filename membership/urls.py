from . import views
from django.urls import path


urlpatterns = [
    path('', views.Membership.as_view(), name='membership'),
]
