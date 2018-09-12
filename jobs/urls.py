from django.conf.urls import url
from django.views.generic import TemplateView

from . import views
from . import feeds

app_name = 'jobs'
urlpatterns = [
    url(r'^$', views.JobList.as_view(), name='job_list'),
    url(r'^feed/rss/$', feeds.JobFeed(), name='job_rss'),
    url(r'^create/$', views.JobCreate.as_view(), name='job_create'),
    url(r'^create-review-comment/$', views.JobReviewCommentCreate.as_view(), name='job_review_comment_create'),
    url(r'^mine/$', views.JobListMine.as_view(), name='job_list_mine'),
    url(r'^review/$', views.JobReview.as_view(), name='job_review'),
    url(r'^moderate/$', views.JobModerateList.as_view(), name='job_moderate'),
    url(r'^thanks/$', TemplateView.as_view(template_name="jobs/job_thanks.html"), name='job_thanks'),
    url(r'^location/telecommute/$', views.JobTelecommute.as_view(), name='job_telecommute'),
    url(r'^location/(?P<slug>[-_\w]+)/$', views.JobListLocation.as_view(), name='job_list_location'),
    url(r'^type/(?P<slug>[-_\w]+)/$', views.JobListType.as_view(), name='job_list_type'),
    url(r'^category/(?P<slug>[-_\w]+)/$', views.JobListCategory.as_view(), name='job_list_category'),
    url(r'^locations/$', views.JobLocations.as_view(), name='job_locations'),
    url(r'^types/$', views.JobTypes.as_view(), name='job_types'),
    url(r'^categories/$', views.JobCategories.as_view(), name='job_categories'),
    url(r'^(?P<pk>\d+)/edit/$', views.JobEdit.as_view(), name='job_edit'),
    url(r'^(?P<pk>\d+)/preview/$', views.JobPreview.as_view(), name='job_preview'),
    url(r'^(?P<pk>\d+)/remove/$', views.JobRemove.as_view(), name='job_remove'),
    url(r'^(?P<pk>\d+)/$', views.JobDetail.as_view(), name='job_detail'),
]
