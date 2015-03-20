from django.conf.urls import url

from .views import box

urlpatterns = [
    url(r'(?P<label>[\w-]+)/$', box, name='box'),
]
