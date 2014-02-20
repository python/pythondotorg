from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import TemplateView
from django.conf import settings


admin.autodiscover()

urlpatterns = patterns('',
    # homepage
    url(r'^$', TemplateView.as_view(template_name="python/index.html"), name='home'),
    url(r'^shell/$', TemplateView.as_view(template_name="python/shell.html"), name='shell'),

    # python section landing pages
    url(r'^about/$', TemplateView.as_view(template_name="python/about.html"), name='about'),
    url(r'^downloads/', include('downloads.urls', namespace='download')),
    url(r'^documentation/$', TemplateView.as_view(template_name="python/documentation.html"), name='documentation'),
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
    url(r'^feedbacks/', include('feedbacks.urls')),
    url(r'^jobs/', include('jobs.urls', namespace='jobs')),
    url(r'^sponsors/', include('sponsors.urls')),
    url(r'^success-stories/', include('successstories.urls')),
    url(r'^users/', include('users.urls', namespace='users')),

    url(r'^psf/records/board/minutes/', include('minutes.urls')),
    url(r'^peps/', include('peps.urls')),
    url(r'^search/', include('haystack.urls')),
    # admin
    url(r'^admin/', include(admin.site.urls)),

    # Fall back on CMS'd pages as the last resort.
    url(r'', include('pages.urls')),
)

if settings.DEBUG:
    # it's a secret to everyone
    urlpatterns += patterns('',
        url(r'^__secret/devfixture/$', 'pydotorg.views.get_dev_fixture', name='pydotorg-devfixture'),
    )

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], 'serve')
    )
