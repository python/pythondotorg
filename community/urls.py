from django.conf.urls import url

from . import views

app_name = 'community'
urlpatterns = [
    url(r'^$', views.PostList.as_view(), name='post_list'),
    url(r'^(?P<pk>\d+)/$', views.PostDetail.as_view(), name='post_detail'),
]
