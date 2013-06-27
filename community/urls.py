from django.conf.urls import url, patterns

from . import views


urlpatterns = patterns('',
    url(r'^$', views.PostList.as_view(), name='post_list'),
    url(r'^(?P<pk>\d+)/$', views.PostDetail.as_view(), name='post_detail'),
)
