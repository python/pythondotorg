from django.conf.urls import url, patterns

from .forms import PageMigrationForm, PageForm
from .views import PageView, PageWizard


urlpatterns = patterns('',
    url(r'wizard/', PageWizard.as_view([PageMigrationForm, PageForm]), name='page_wizard'),
    url(r'(?P<path>.+)/$', PageView.as_view(), name='page_detail'),
)
