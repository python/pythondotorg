from . import views
from django.urls import path, re_path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', views.BlogHome.as_view(), name='blog'),
    # Redirect all requests from pythoninsider.blogspot.com to blog.python.org
    re_path(r'^(?P<path>.*)$', RedirectView.as_view(url='https://blog.python.org/%(path)s', permanent=True)),
]
