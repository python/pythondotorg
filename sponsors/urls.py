from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^$', views.SponsorList.as_view(), name='sponsor_list'),
)
