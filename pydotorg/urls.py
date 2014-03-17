from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView
from django.conf import settings

from . import views
from .urls_api import v1_api

admin.autodiscover()

urlpatterns = patterns('',
    # homepage
    url(r'^$', views.IndexView.as_view(), name='home'),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    url(r'^shell/$', TemplateView.as_view(template_name="python/shell.html"), name='shell'),

    # python section landing pages
    url(r'^about/$', TemplateView.as_view(template_name="python/about.html"), name='about'),
    url(r'^downloads/', include('downloads.urls', namespace='download')),
    url(r'^doc/$', TemplateView.as_view(template_name="python/documentation.html"), name='documentation'),
    #url(r'^community/$', TemplateView.as_view(template_name="python/community.html"), name='community'),
    url(r'^blog/$', TemplateView.as_view(template_name="python/blog.html"), name='blog'),
    url(r'^blogs/$', include('blogs.urls')),
    url(r'^inner/$', TemplateView.as_view(template_name="python/inner.html"), name='inner'),

    # other section landing pages
    url(r'^psf-landing/$', TemplateView.as_view(template_name="psf/index.html"), name='psf-landing'),
    url(r'^docs-landing/$', TemplateView.as_view(template_name="docs/index.html"), name='docs-landing'),
    url(r'^pypl-landing/$', TemplateView.as_view(template_name="pypl/index.html"), name='pypl-landing'),
    url(r'^shop-landing/$', TemplateView.as_view(template_name="shop/index.html"), name='shop-landing'),

    url(r'^accounts/', include('allauth.urls')),
    url(r'^box/', include('boxes.urls')),
    url(r'^comments/', include('django_comments_xtd.urls')),
    url(r'^community/', include('community.urls', namespace='community')),
    url(r'^events/', include('events.urls', namespace='events')),
    url(r'^newjobs/', include('jobs.urls', namespace='jobs')),
    url(r'^sponsors/', include('sponsors.urls')),
    url(r'^success-stories/', include('successstories.urls')),
    url(r'^users/', include('users.urls', namespace='users')),

    url(r'^psf/records/board/minutes/', include('minutes.urls')),
    url(r'^peps/', include('peps.urls')),
    url(r'^search/', include('haystack.urls')),
    # admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # api
    url(r'^api/', include(v1_api.urls)),

    # it's a secret to everyone
    url(r'^__secret/devfixture/$', 'pydotorg.views.get_dev_fixture', name='pydotorg-devfixture'),

    # Fall back on CMS'd pages as the last resort.
    url(r'', include('pages.urls')),
)

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'serve')
    )
