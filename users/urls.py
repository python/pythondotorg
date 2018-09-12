from django.conf.urls import url

from . import views


app_name = 'users'
urlpatterns = [
    url(r'^edit/$', views.UserUpdate.as_view(), name='user_profile_edit'),
    url(r'^membership/$', views.MembershipCreate.as_view(), name='user_membership_create'),
    url(r'^membership/edit/$', views.MembershipUpdate.as_view(), name='user_membership_edit'),
    url(r'^membership/delete/(?P<slug>[-_\w\@\.+]+)/$', views.MembershipDeleteView.as_view(), name='user_membership_delete'),
    url(r'^membership/thanks/$', views.MembershipThanks.as_view(), name='user_membership_thanks'),
    url(r'^membership/affirm/$', views.MembershipVoteAffirm.as_view(), name='membership_affirm_vote'),
    url(r'^membership/affirm/done/$', views.MembershipVoteAffirmDone.as_view(), name='membership_affirm_vote_done'),
    url(r'^(?P<slug>[-_\w\@\.+]+)/delete/$', views.UserDeleteView.as_view(), name='user_delete'),
    url(r'^(?P<slug>[-_\w\@\.+]+)/$', views.UserDetail.as_view(), name='user_detail'),
]
