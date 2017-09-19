from django.conf import settings
from django.utils.encoding import force_text
from django.http import HttpResponseForbidden
from django.template import Context, Engine, TemplateDoesNotExist, loader
from django.utils.translation import ugettext as _
from django.utils.version import get_docs_version
from django.views.csrf import CSRF_FAILURE_TEMPLATE, CSRF_FAILURE_TEMPLATE_NAME
from django.utils.http import is_same_domain
from django.views.generic.base import TemplateView

from urllib.parse import urlparse

from codesamples.models import CodeSample
from downloads.models import Release


def custom_csrf_failure(request, reason=''):
    from django.middleware.csrf import REASON_NO_REFERER, REASON_NO_CSRF_COOKIE
    referer = urlparse(force_text(
        request.META.get('HTTP_REFERER'),
        strings_only=True,
        errors='replace'
    ))
    more = {
        'server_port': request.get_port(),
        'server_host': request.get_host(),
        'good_hosts': settings.CSRF_TRUSTED_ORIGINS,
        'good_referer': settings.CSRF_COOKIE_DOMAIN,
        'referer': referer,
        'same_domain': is_same_domain(referer.netloc, settings.CSRF_COOKIE_DOMAIN)
    }
    c = {
        'title': _("Forbidden"),
        'main': _("CSRF verification failed. Request aborted."),
        'reason': reason,
        'no_referer': reason == REASON_NO_REFERER,
        'no_referer1': _(
            "You are seeing this message because this HTTPS site requires a "
            "'Referer header' to be sent by your Web browser, but none was "
            "sent. This header is required for security reasons, to ensure "
            "that your browser is not being hijacked by third parties."),
        'no_referer2': _(
            "If you have configured your browser to disable 'Referer' headers, "
            "please re-enable them, at least for this site, or for HTTPS "
            "connections, or for 'same-origin' requests."),
        'no_cookie': reason == REASON_NO_CSRF_COOKIE,
        'no_cookie1': _(
            "You are seeing this message because this site requires a CSRF "
            "cookie when submitting forms. This cookie is required for "
            "security reasons, to ensure that your browser is not being "
            "hijacked by third parties."),
        'no_cookie2': _(
            "If you have configured your browser to disable cookies, please "
            "re-enable them, at least for this site, or for 'same-origin' "
            "requests."),
        # TODO: Customized this to get more information.
        'DEBUG': True,
        'docs_version': get_docs_version(),
        'more': """
        server_port: %(server_port)s<br>
        server_host: %(server_host)s<br>
        good_hosts: %(good_hosts)s<br>
        good_referer: %(good_referer)s<br>
        referer: %(referer)s<br>
        same_domain: %(same_domain)s<br>
        """ % more,
    }
    try:
        t = loader.get_template(CSRF_FAILURE_TEMPLATE_NAME)
    except TemplateDoesNotExist:
        # If the default template doesn't exist, use the string template.
        t = Engine().from_string(CSRF_FAILURE_TEMPLATE + """
        {{ more }}
        """)
        c = Context(c)
    return HttpResponseForbidden(t.render(c), content_type='text/html')


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'code_samples': CodeSample.objects.published()[:5],
        })
        return context


class DocumentationIndexView(TemplateView):
    template_name = 'python/documentation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'latest_python2': Release.objects.latest_python2(),
            'latest_python3': Release.objects.latest_python3(),
        })
        return context
