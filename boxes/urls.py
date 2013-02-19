from django.conf.urls import url, patterns
from .views import box

urlpatterns = patterns('',
    url(r'(?P<label>[\w-]+)/$', box, name='box'),
)
