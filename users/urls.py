from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^$', views.UserList.as_view(), name='user_list'),
    url(r'^(?P<slug>[-_\w]+)/$', views.UserDetail.as_view(), name='user_detail'),
    url(r'^(?P<slug>[-_\w]+)/edit/$', views.UserUpdate.as_view(), name='user_profile_edit'),
    url(r'^(?P<slug>[-_\w]+)/membership/$', views.MembershipUpdate.as_view(), name='user_membership_edit'),
)
