from django.conf.urls import handler404
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.urls import include
from django.urls import path, re_path
from django.views.generic.base import TemplateView
from django.conf import settings

from cms.views import custom_404
from users.views import HoneypotSignupView, CustomPasswordChangeView

from . import views, urls_api

handler404 = custom_404

urlpatterns = [
    # homepage
    path('', views.IndexView.as_view(), name='home'),
    re_path(r'^_health/?', views.health, name='health'),
    path('authenticated', views.AuthenticatedView.as_view(), name='authenticated'),
    re_path(r'^humans.txt$', TemplateView.as_view(template_name='humans.txt', content_type='text/plain')),
    re_path(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('shell/', TemplateView.as_view(template_name="python/shell.html"), name='shell'),

    # python section landing pages
    path('about/', TemplateView.as_view(template_name="python/about.html"), name='about'),

    # duplicated downloads to getit to bypass China's firewall. See
    # https://github.com/python/pythondotorg/issues/427 for more info.
    path('getit/', include('downloads.urls', namespace='getit')),
    path('downloads/', include('downloads.urls', namespace='download')),
    path('doc/', views.DocumentationIndexView.as_view(), name='documentation'),
    path('blogs/', include('blogs.urls')),
    path('inner/', TemplateView.as_view(template_name="python/inner.html"), name='inner'),

    # other section landing pages
    path('psf-landing/', TemplateView.as_view(template_name="psf/index.html"), name='psf-landing'),
    path('psf/sponsors/', TemplateView.as_view(template_name="psf/sponsors-list.html"), name='psf-sponsors'),
    path('docs-landing/', TemplateView.as_view(template_name="docs/index.html"), name='docs-landing'),
    path('pypl-landing/', TemplateView.as_view(template_name="pypl/index.html"), name='pypl-landing'),
    path('shop-landing/', TemplateView.as_view(template_name="shop/index.html"), name='shop-landing'),

    # Override /accounts/signup/ to add Honeypot.
    path('accounts/signup/', HoneypotSignupView.as_view()),
    # Override /accounts/password/change/ to add Honeypot
    # and change success URL.
    path('accounts/password/change/', CustomPasswordChangeView.as_view(),
        name='account_change_password'),
    path('accounts/', include('allauth.urls')),
    path('box/', include('boxes.urls')),
    path('community/', include('community.urls', namespace='community')),
    path('community/microbit/', TemplateView.as_view(template_name="community/microbit.html"), name='microbit'),
    path('events/', include('events.urls', namespace='events')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('sponsors/', include('sponsors.urls')),
    path('success-stories/', include('successstories.urls')),
    path('users/', include('users.urls', namespace='users')),

    path('psf/records/board/minutes/', include('minutes.urls')),
    path('membership/', include('membership.urls')),
    path('search/', include('haystack.urls')),
    path('nominations/', include('nominations.urls')),
    # admin
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),

    # api
    path('api/', include(urls_api.v1_api.urls)),
    path('api/v2/', include(urls_api.router.urls)),
    path('api/v2/', include(urls_api)),

    # storage migration
    re_path(r'^m/(?P<url>.*)/$', views.MediaMigrationView.as_view(prefix='media'), name='media_migration_view'),
]

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
