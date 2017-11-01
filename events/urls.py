from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'calendars/$', views.CalendarList.as_view(), name='calendar_list'),
    url(r'^submit/$', views.EventSubmit.as_view(), name='event_submit'),
    url(r'^submit/thanks/$', TemplateView.as_view(template_name='events/event_form_thanks.html'), name='event_thanks'),
    url(r'(?P<calendar_slug>[-_\w]+)/categories/(?P<slug>[-_\w]+)/$', views.EventListByCategory.as_view(), name='eventlist_category'),
    url(r'(?P<calendar_slug>[-_\w]+)/categories/$', views.EventCategoryList.as_view(), name='eventcategory_list'),
    url(r'(?P<calendar_slug>[-_\w]+)/locations/(?P<pk>\d+)/$', views.EventListByLocation.as_view(), name='eventlist_location'),
    url(r'(?P<calendar_slug>[-_\w]+)/locations/$', views.EventLocationList.as_view(), name='eventlocation_list'),
    url(r'(?P<calendar_slug>[-_\w]+)/date/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$', views.EventListByDate.as_view(), name='eventlist_date'),
    url(r'(?P<calendar_slug>[-_\w]+)/(?P<pk>\d+)/$', views.EventDetail.as_view(), name='event_detail'),
    url(r'(?P<calendar_slug>[-_\w]+)/past/$', views.PastEventList.as_view(), name='event_list_past'),
    url(r'(?P<calendar_slug>[-_\w]+)/$', views.EventList.as_view(), name='event_list'),
    url(r'$', views.EventHomepage.as_view(), name='events'),
]
