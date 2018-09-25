import requests

from urllib.parse import urljoin

from django.conf import settings


def purge_url(*paths):
    """
    Purge the Fastly.com URL cache for each given path.
    """
    api_key = getattr(settings, 'FASTLY_API_KEY', None)
    if not api_key or settings.DEBUG:
        return

    for path in paths:
        requests.request(
            'PURGE',
            urljoin('https://www.python.org', path),
            headers={'Fastly-Key': api_key},
        )
