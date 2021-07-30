from django.conf.urls import include, url, handler404
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.generic.base import TemplateView, RedirectView
from django.conf import settings

from cms.views import custom_404
from users.views import HoneypotSignupView, CustomPasswordChangeView

from . import views
from .urls_api import v1_api, router

handler404 = custom_404

urlpatterns = [
    # homepage
    url(r'^$', views.IndexView.as_view(), name='home'),
    url(r'^authenticated$', views.AuthenticatedView.as_view(), name='authenticated'),
    url(r'^humans.txt$', TemplateView.as_view(template_name='humans.txt', content_type='text/plain')),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    url(r'^shell/$', TemplateView.as_view(template_name="python/shell.html"), name='shell'),

    # python section landing pages
    url(r'^about/$', TemplateView.as_view(template_name="python/about.html"), name='about'),

    # Redirect old download links to new downloads pages
    url(r'^download/$', RedirectView.as_view(url='https://www.python.org/downloads/', permanent=True)),
    url(r'^download/source/$', RedirectView.as_view(url='https://www.python.org/downloads/source/', permanent=True)),
    url(r'^download/mac/$', RedirectView.as_view(url='https://www.python.org/downloads/macos/', permanent=True)),
    url(r'^download/windows/$', RedirectView.as_view(url='https://www.python.org/downloads/windows/', permanent=True)),

    # duplicated downloads to getit to bypass China's firewall. See
    # https://github.com/python/pythondotorg/issues/427 for more info.
    url(r'^getit/', include('downloads.urls', namespace='getit')),
    url(r'^downloads/', include('downloads.urls', namespace='download')),
    url(r'^doc/$', views.DocumentationIndexView.as_view(), name='documentation'),
    url(r'^blog/$', RedirectView.as_view(url='/blogs/', permanent=True)),
    url(r'^blogs/', include('blogs.urls')),
    url(r'^inner/$', TemplateView.as_view(template_name="python/inner.html"), name='inner'),

    # other section landing pages
    url(r'^psf-landing/$', TemplateView.as_view(template_name="psf/index.html"), name='psf-landing'),
    url(r'^psf/sponsors/$', TemplateView.as_view(template_name="psf/sponsors-list.html"), name='psf-sponsors'),
    url(r'^docs-landing/$', TemplateView.as_view(template_name="docs/index.html"), name='docs-landing'),
    url(r'^pypl-landing/$', TemplateView.as_view(template_name="pypl/index.html"), name='pypl-landing'),
    url(r'^shop-landing/$', TemplateView.as_view(template_name="shop/index.html"), name='shop-landing'),

    # Override /accounts/signup/ to add Honeypot.
    url(r'^accounts/signup/', HoneypotSignupView.as_view()),
    # Override /accounts/password/change/ to add Honeypot
    # and change success URL.
    url(r'^accounts/password/change/$', CustomPasswordChangeView.as_view(),
        name='account_change_password'),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^box/', include('boxes.urls')),
    url(r'^community/', include('community.urls', namespace='community')),
    url(r'^community/microbit/$', TemplateView.as_view(template_name="community/microbit.html"), name='microbit'),
    url(r'^events/', include('events.urls', namespace='events')),
    url(r'^jobs/', include('jobs.urls', namespace='jobs')),
    url(r'^sponsors/', include('sponsors.urls')),
    url(r'^success-stories/', include('successstories.urls')),
    url(r'^users/', include('users.urls', namespace='users')),

    url(r'^psf/records/board/minutes/', include('minutes.urls')),
    url(r'^membership/', include('membership.urls')),
    url(r'^search/', include('haystack.urls')),
    url(r'^nominations/', include('nominations.urls')),
    # admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),

    # api
    url(r'^api/', include(v1_api.urls)),
    url(r'^api/v2/', include(router.urls)),

    # storage migration
    url(r'^m/(?P<url>.*)/$', views.MediaMigrationView.as_view(prefix='media'), name='media_migration_view'),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
