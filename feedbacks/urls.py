from django.conf.urls import patterns, url

from .views import FeedbackComplete, FeedbackCreate


urlpatterns = patterns('',
    url(r'^$', FeedbackCreate.as_view(), name='feedback_create'),
    url(r'^complete/$', FeedbackComplete.as_view(), name='feedback_complete'),
)
