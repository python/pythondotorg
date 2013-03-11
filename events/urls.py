from django.conf.urls import url, patterns
from . import views

urlpatterns = patterns('',
    url(r'date/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$', views.EventListByDate.as_view(), name='eventlist_date'),
    url(r'categories/(?P<slug>[-_\w]+)/$', views.EventListByCategory.as_view(), name='eventlist_category'),
    url(r'categories/$', views.EventCategoryList.as_view(), name='eventcategory_list'),
    url(r'locations/(?P<pk>\d+)/$', views.EventListByLocation.as_view(), name='eventlist_location'),
    url(r'locations/$', views.EventLocationList.as_view(), name='eventlocation_list'),
    url(r'(?P<pk>\d+)/$', views.EventDetail.as_view(), name='event_detail'),
    url(r'$', views.EventList.as_view(), name='event_list'),
)
