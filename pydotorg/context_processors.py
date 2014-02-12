from django.conf import settings
from django.core.urlresolvers import resolve


def site_info(request):
    return {'SITE_INFO': settings.SITE_VARIABLES}

def url_name(request):
    match = resolve(request.path)
    namespace, url_name  = match.namespace, match.url_name
    if namespace:
        url_name = "%s:%s" % (namespace, url_name)
    return {'URL_NAMESPACE': namespace, 'URL_NAME': url_name}
