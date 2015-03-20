from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.StoryList.as_view(), name='success_story_list'),
    url(r'^create/$', views.StoryCreate.as_view(), name='success_story_create'),
    url(r'^(?P<slug>[-_\w]+)/$', views.StoryDetail.as_view(), name='success_story_detail'),
    url(r'^category/(?P<slug>[-_\w]+)/$', views.StoryListCategory.as_view(), name='success_story_list_category'),
]
