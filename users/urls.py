from django.conf.urls import url
from django.contrib.auth.views import password_change

from . import views


urlpatterns = [
    url(r'^$', views.UserList.as_view(), name='user_list'),
    url(r'^edit/$', views.UserUpdate.as_view(), name='user_profile_edit'),
    url(r'^change-password/$', password_change, name='user_change_password', kwargs={
        'template_name': 'users/password_change_form.html',
        'post_change_redirect':  '/users/edit/',
    }),
    url(r'^membership/$', views.MembershipCreate.as_view(), name='user_membership_create'),
    url(r'^membership/edit/$', views.MembershipUpdate.as_view(), name='user_membership_edit'),
    url(r'^membership/delete/(?P<slug>[-_\w\@\.+]+)/$', views.MembershipDeleteView.as_view(), name='user_membership_delete'),
    url(r'^membership/thanks/$', views.MembershipThanks.as_view(), name='user_membership_thanks'),
    url(r'^membership/affirm/$', views.MembershipVoteAffirm.as_view(), name='membership_affirm_vote'),
    url(r'^membership/affirm/done/$', views.MembershipVoteAffirmDone.as_view(), name='membership_affirm_vote_done'),
    url(r'^(?P<slug>[-_\w\@\.+]+)/delete/$', views.UserDeleteView.as_view(), name='user_delete'),
    url(r'^(?P<slug>[-_\w\@\.+]+)/$', views.UserDetail.as_view(), name='user_detail'),
]
