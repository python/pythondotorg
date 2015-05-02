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
    url(r'^membership/thanks/$', views.MembershipThanks.as_view(), name='user_membership_thanks'),
    url(r'^(?P<slug>[-_\w\@\.+]+)/$', views.UserDetail.as_view(), name='user_detail'),
]
