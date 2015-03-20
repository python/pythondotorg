from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.BlogHome.as_view(), name='blog'),
]
