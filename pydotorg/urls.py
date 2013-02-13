from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name="python/index.html"), name='home'),
    url(r'^about/$', TemplateView.as_view(template_name="python/about.html"), name='about'),
    url(r'^download/$', TemplateView.as_view(template_name="python/download.html"), name='download'),
    url(r'^documentation/$', TemplateView.as_view(template_name="python/documentation.html"), name='documentation'),
    url(r'^community/$', TemplateView.as_view(template_name="python/community.html"), name='community'),
    url(r'^success-stories/$', TemplateView.as_view(template_name="python/success-stories.html"), name='success-stories'),
    url(r'^blog/$', TemplateView.as_view(template_name="python/blog.html"), name='blog'),
    url(r'^events/$', TemplateView.as_view(template_name="python/events.html"), name='events'),
    url(r'^inner/$', TemplateView.as_view(template_name="python/inner.html"), name='inner'),
    
    url(r'^psf-landing/$', TemplateView.as_view(template_name="psf/index.html"), name='psf-landing'),
    url(r'^docs-landing/$', TemplateView.as_view(template_name="docs/index.html"), name='docs-landing'),
    url(r'^pypl-landing/$', TemplateView.as_view(template_name="pypl/index.html"), name='pypl-landing'),
    url(r'^jobs-landing/$', TemplateView.as_view(template_name="jobs/index.html"), name='jobs-landing'),
    url(r'^shop-landing/$', TemplateView.as_view(template_name="shop/index.html"), name='shop-landing'),
    
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('pages.urls')),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
