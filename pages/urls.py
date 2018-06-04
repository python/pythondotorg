from django.conf.urls import url

from .views import PageView

urls = 'pages'
urlpatterns = [
    url(r'(?P<path>.+)/$', PageView.as_view(), name='page_detail'),
]
