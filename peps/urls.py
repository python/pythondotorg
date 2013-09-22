from django.conf.urls import patterns, url

from . import views
from .feeds import LatestPepEntries

urlpatterns = patterns('',
    url(r'^$', views.PepListView.as_view(), name='pep_list'),
    url(r'^rss/latest/$', LatestPepEntries(), name='pep_rss'),
)
