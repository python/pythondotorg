from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(r'^$', views.UserList.as_view(), name='user_list'),
    url(r'^edit/$', views.UserUpdate.as_view(), name='user_profile_edit'),
    url(r'^membership/$', views.MembershipUpdate.as_view(), name='user_membership_edit'),
    url(r'^membership/thanks/$', views.MembershipThanks.as_view(), name='user_membership_thanks'),
    url(r'^(?P<slug>[-_\w]+)/$', views.UserDetail.as_view(), name='user_detail'),
)
