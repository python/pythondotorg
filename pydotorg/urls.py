from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="pages/home.html"), name='home'),
    url(r'^about/$', TemplateView.as_view(template_name="pages/about.html"), name='about'),
    url(r'^download/$', TemplateView.as_view(template_name="pages/download.html"), name='download'),
    url(r'^documentation/$', TemplateView.as_view(template_name="pages/documentation.html"), name='documentation'),
    url(r'^community/$', TemplateView.as_view(template_name="pages/community.html"), name='community'),
    url(r'^success-stories/$', TemplateView.as_view(template_name="pages/success-stories.html"), name='success-stories'),
    url(r'^blog/$', TemplateView.as_view(template_name="pages/blog.html"), name='blog'),
    url(r'^events/$', TemplateView.as_view(template_name="pages/events.html"), name='events'),
    
    url(r'^inner/$', TemplateView.as_view(template_name="inner.html"), name='inner'),
    
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('pages.urls')),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
