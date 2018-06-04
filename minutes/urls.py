from django.conf.urls import url

from .feeds import MinutesFeed
from . import views


urlpatterns = [
    url(r'^$', views.MinutesList.as_view(), name='minutes_list'),
    url(r'^feed/$', MinutesFeed(), name='minutes_feed'),
    url(r'^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})/$', views.MinutesDetail.as_view(), name='minutes_detail'),
]
