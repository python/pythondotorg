from django.conf.urls import patterns, url
from django.contrib.auth.views import login, logout

from . import views


urlpatterns = patterns('',
    url(r'^signup/$', views.SignupView.as_view(), name='signup'),
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
)
