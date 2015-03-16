from django.conf.urls import patterns, include, url, handler404
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.views.generic.base import TemplateView, RedirectView
from django.conf import settings

from cms.views import custom_404
from . import views
from .urls_api import v1_api

admin.autodiscover()

handler404 = custom_404

# Hack to fix admindocs bug. See https://code.djangoproject.com/ticket/6681.
# Please remove this when we upgrade to Django 1.7.
from django.contrib.admindocs import utils as ad_utils
parse_rst = """
def parse_rst(text, default_reference_context, thing_being_parsed=None):
    \"\"\"
    Convert the string from reST to an XHTML fragment.
    \"\"\"
    overrides = {
        'doctitle_xform': True,
        'inital_header_level': 3,
        "default_reference_context": default_reference_context,
        "link_base": reverse('django-admindocs-docroot').rstrip('/')
    }
    if thing_being_parsed:
        thing_being_parsed = force_bytes("<%s>" % thing_being_parsed)
    # Wrap ``text`` in some reST that sets the default role to ``cmsreference``,
    # then restores it.
    source = \"\"\"
.. default-role:: cmsreference

%s

.. default-role::
\"\"\"
    parts = docutils.core.publish_parts(source % text,
                source_path=thing_being_parsed, destination_path=None,
                writer_name='html', settings_overrides=overrides)
    return mark_safe(parts['fragment'])

def create_reference_role(rolename, urlbase):
    def _role(name, rawtext, text, lineno, inliner, options=None, content=None):
        if options is None:
            options = {}
        if content is None:
            content = []
        node = docutils.nodes.reference(rawtext, text, refuri=(urlbase % (inliner.document.settings.link_base, text.lower())), **options)
        return [node], []
    docutils.parsers.rst.roles.register_canonical_role(rolename, _role)


def default_reference_role(name, rawtext, text, lineno, inliner, options=None, content=None):
    if options is None:
        options = {}
    if content is None:
        content = []
    context = inliner.document.settings.default_reference_context
    node = docutils.nodes.reference(rawtext, text, refuri=(ROLES[context] % (inliner.document.settings.link_base, text.lower())), **options)
    return [node], []
"""
exec(parse_rst, ad_utils.__dict__)
import docutils.parsers.rst.roles
docutils.parsers.rst.roles.DEFAULT_INTERPRETED_ROLE = 'title-reference'


urlpatterns = patterns('',
    # homepage
    url(r'^$', views.IndexView.as_view(), name='home'),
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    url(r'^shell/$', TemplateView.as_view(template_name="python/shell.html"), name='shell'),

    # python section landing pages
    url(r'^about/$', TemplateView.as_view(template_name="python/about.html"), name='about'),

    # Redirect old download links to new downloads pages
    url(r'^download/$', RedirectView.as_view(url='https://www.python.org/downloads/')),
    url(r'^download/source/$', RedirectView.as_view(url='https://www.python.org/downloads/source/')),
    url(r'^download/mac/$', RedirectView.as_view(url='https://www.python.org/downloads/mac-osx/')),
    url(r'^download/windows/$', RedirectView.as_view(url='https://www.python.org/downloads/windows/')),

    # duplicated downloads to getit to bypass China's firewall. See
    # https://github.com/python/pythondotorg/issues/427 for more info.
    url(r'^getit/', include('downloads.urls', namespace='getit')),
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
    url(r'^jobs/', include('jobs.urls', namespace='jobs')),
    url(r'^newjobs/', include('jobs.urls', namespace='jobs')),
    url(r'^sponsors/', include('sponsors.urls')),
    url(r'^success-stories/', include('successstories.urls')),
    url(r'^users/', include('users.urls', namespace='users')),

    url(r'^psf/records/board/minutes/', include('minutes.urls')),
    url(r'^search/', include('haystack.urls')),
    # admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # api
    url(r'^api/', include(v1_api.urls)),

    # it's a secret to everyone
    url(r'^__secret/devfixture/$', 'pydotorg.views.get_dev_fixture', name='pydotorg-devfixture'),
)

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
