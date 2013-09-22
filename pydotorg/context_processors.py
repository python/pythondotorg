from django.conf import settings


def site_info(request):
    return {'SITE_INFO': settings.SITE_VARIABLES}
