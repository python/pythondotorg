from django.conf.urls import url, patterns
from . import views

urlpatterns = patterns('',
    url(r'location/(?P<slug>[-_\w]+)/$', views.JobListLocation.as_view(), name="job_list_location"),
    url(r'type/(?P<slug>[-_\w]+)/$', views.JobListType.as_view(), name="job_list_type"),
    url(r'category/(?P<slug>[-_\w]+)/$', views.JobListCategory.as_view(), name="job_list_category"),
    url(r'company/(?P<slug>[-_\w]+)/$', views.JobListCompany.as_view(), name="job_list_company"),
    url(r'create/$', views.JobCreate.as_view(), name="job_create"),
    url(r'(?P<pk>\d+)/$', views.JobDetail.as_view(), name="job_detail"),
    url(r'$', views.JobList.as_view(), name='job_list'),
)
