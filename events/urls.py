from django.views.generic import TemplateView

from . import views
from django.urls import path, re_path

app_name = 'events'
urlpatterns = [
    path('calendars/', views.CalendarList.as_view(), name='calendar_list'),
    path('submit/', views.EventSubmit.as_view(), name='event_submit'),
    path('submit/thanks/', TemplateView.as_view(template_name='events/event_form_thanks.html'), name='event_thanks'),
    path('<slug:calendar_slug>/categories/<slug:slug>/', views.EventListByCategory.as_view(), name='eventlist_category'),
    path('<slug:calendar_slug>/categories/', views.EventCategoryList.as_view(), name='eventcategory_list'),
    path('<slug:calendar_slug>/locations/<int:pk>/', views.EventListByLocation.as_view(), name='eventlist_location'),
    path('<slug:calendar_slug>/locations/', views.EventLocationList.as_view(), name='eventlocation_list'),
    re_path(r'(?P<calendar_slug>[-a-zA-Z0-9_]+)/date/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$', views.EventListByDate.as_view(), name='eventlist_date'),
    path('<slug:calendar_slug>/<int:pk>/', views.EventDetail.as_view(), name='event_detail'),
    path('<slug:calendar_slug>/past/', views.PastEventList.as_view(), name='event_list_past'),
    path('<slug:calendar_slug>/', views.EventList.as_view(), name='event_list'),
    path('', views.EventHomepage.as_view(), name='events'),
]
