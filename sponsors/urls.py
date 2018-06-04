from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.SponsorList.as_view(), name='sponsor_list'),
]
