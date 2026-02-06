from django.urls import path, re_path

from . import views
from .feeds import MinutesFeed

urlpatterns = [
    path("", views.MinutesList.as_view(), name="minutes_list"),
    path("feed/", MinutesFeed(), name="minutes_feed"),
    re_path(
        r"^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})/$",
        views.MinutesDetail.as_view(),
        name="minutes_detail",
    ),
]
