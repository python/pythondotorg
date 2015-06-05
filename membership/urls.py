from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.Membership.as_view(), name='membership'),
]
