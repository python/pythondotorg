from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^$', views.PepListView.as_view(), name='pep_list'),
)
