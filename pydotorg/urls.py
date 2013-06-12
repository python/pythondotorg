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

    url(r'^accounts/', include('allauth.urls')),
    url(r'^box/', include('boxes.urls')),
    url(r'^comments/', include('django_comments_xtd.urls')),
    url(r'^events/', include('events.urls', namespace='events')),
    url(r'^feedbacks/', include('feedbacks.urls')),
    url(r'^jobs/', include('jobs.urls', namespace='jobs')),
    url(r'^sponsors/', include('sponsors.urls')),
    url(r'^success-stories/', include('successstories.urls')),
    url(r'^users/', include('users.urls', namespace='users')),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # it's a secret to everyone
    url(r'^__secret/devfixture/$', 'pydotorg.views.get_dev_fixture', name='pydotorg-devfixture'),

    # Fall back on CMS'd pages as the last resort.
    url(r'', include('pages.urls')),
)

urlpatterns += staticfiles_urlpatterns()
