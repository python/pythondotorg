from django.views.generic import TemplateView

from . import views
from . import feeds
from django.urls import path

app_name = 'jobs'
urlpatterns = [
    path('', views.JobList.as_view(), name='job_list'),
    path('feed/rss/', feeds.JobFeed(), name='job_rss'),
    path('create/', views.JobCreate.as_view(), name='job_create'),
    path('create-review-comment/', views.JobReviewCommentCreate.as_view(), name='job_review_comment_create'),
    path('mine/', views.JobListMine.as_view(), name='job_list_mine'),
    path('review/', views.JobReview.as_view(), name='job_review'),
    path('moderate/', views.JobModerateList.as_view(), name='job_moderate'),
    path('thanks/', TemplateView.as_view(template_name="jobs/job_thanks.html"), name='job_thanks'),
    path('location/telecommute/', views.JobTelecommute.as_view(), name='job_telecommute'),
    path('location/<slug:slug>/', views.JobListLocation.as_view(), name='job_list_location'),
    path('type/<slug:slug>/', views.JobListType.as_view(), name='job_list_type'),
    path('category/<slug:slug>/', views.JobListCategory.as_view(), name='job_list_category'),
    path('locations/', views.JobLocations.as_view(), name='job_locations'),
    path('types/', views.JobTypes.as_view(), name='job_types'),
    path('categories/', views.JobCategories.as_view(), name='job_categories'),
    path('<int:pk>/edit/', views.JobEdit.as_view(), name='job_edit'),
    path('<int:pk>/preview/', views.JobPreview.as_view(), name='job_preview'),
    path('<int:pk>/remove/', views.JobRemove.as_view(), name='job_remove'),
    path('<int:pk>/', views.JobDetail.as_view(), name='job_detail'),
]
