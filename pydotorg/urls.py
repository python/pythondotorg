from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView


admin.autodiscover()

urlpatterns = patterns('',
    # homepage
    url(r'^$', TemplateView.as_view(template_name="python/index.html"), name='home'),

    # python section landing pages
    url(r'^about/$', TemplateView.as_view(template_name="python/about.html"), name='about'),
    url(r'^download/$', TemplateView.as_view(template_name="python/download.html"), name='download'),
    url(r'^documentation/$', TemplateView.as_view(template_name="python/documentation.html"), name='documentation'),
    url(r'^community/$', TemplateView.as_view(template_name="python/community.html"), name='community'),
    url(r'^blog/$', TemplateView.as_view(template_name="python/blog.html"), name='blog'),
    url(r'^inner/$', TemplateView.as_view(template_name="python/inner.html"), name='inner'),

    # other section landing pages
    url(r'^psf-landing/$', TemplateView.as_view(template_name="psf/index.html"), name='psf-landing'),
    url(r'^docs-landing/$', TemplateView.as_view(template_name="docs/index.html"), name='docs-landing'),
    url(r'^pypl-landing/$', TemplateView.as_view(template_name="pypl/index.html"), name='pypl-landing'),
    url(r'^shop-landing/$', TemplateView.as_view(template_name="shop/index.html"), name='shop-landing'),

    # supernav menus
    url(r'^supernav-python-about/$', TemplateView.as_view(template_name="components/supernav-python-about.html"), name='supernav-python-about'),
    url(r'^supernav-python-downloads/$', TemplateView.as_view(template_name="components/supernav-python-downloads.html"), name='supernav-python-downloads'),
    url(r'^supernav-python-documentation/$', TemplateView.as_view(template_name="components/supernav-python-documentation.html"), name='supernav-python-documentation'),
    url(r'^supernav-python-community/$', TemplateView.as_view(template_name="components/supernav-python-community.html"), name='supernav-python-community'),
    url(r'^supernav-python-success-stories/$', TemplateView.as_view(template_name="components/supernav-python-success-stories.html"), name='supernav-python-success-stories'),
    url(r'^supernav-python-blog/$', TemplateView.as_view(template_name="components/supernav-python-blog.html"), name='supernav-python-blog'),
    url(r'^supernav-python-events/$', TemplateView.as_view(template_name="components/supernav-python-events.html"), name='supernav-python-events'),

    url(r'^jobs/', include('jobs.urls', namespace='jobs')),
    url(r'^box/', include('boxes.urls')),
    url(r'^events/', include('events.urls', namespace='events')),
    url(r'^sponsors/', include('sponsors.urls')),
    url(r'^success-stories/', include('successstories.urls')),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # Fall back on CMS'd pages as the last resort.
    url(r'', include('pages.urls')),
)

urlpatterns += staticfiles_urlpatterns()
