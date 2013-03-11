from django.conf.urls import url, patterns
from .views import PageView

urlpatterns = patterns('',
    url(r'(?P<path>.+)/$', PageView.as_view(), name='page_detail'),
)
