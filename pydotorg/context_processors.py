from django.conf import settings
from django.urls import resolve, Resolver404


def site_info(request):
    return {'SITE_INFO': settings.SITE_VARIABLES}


def url_name(request):
    try:
        match = resolve(request.path)
    except Resolver404:
        return {}
    else:
        namespace, url_name  = match.namespace, match.url_name
        if namespace:
            url_name = "%s:%s" % (namespace, url_name)
        return {'URL_NAMESPACE': namespace, 'URL_NAME': url_name}


def get_host_with_scheme(request):
    return {
        'GET_HOST_WITH_SCHEME': request.build_absolute_uri('/').rstrip('/'),
    }


def blog_url(request):
    return {
        'BLOG_URL': settings.PYTHON_BLOG_URL,
    }
