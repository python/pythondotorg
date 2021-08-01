from . import views
from django.urls import path


urlpatterns = [
    path('', views.StoryList.as_view(), name='success_story_list'),
    path('create/', views.StoryCreate.as_view(), name='success_story_create'),
    path('<slug:slug>/', views.StoryDetail.as_view(), name='success_story_detail'),
    path('category/<slug:slug>/', views.StoryListCategory.as_view(), name='success_story_list_category'),
]
