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

    with requests.session() as session:
        session.headers['Fastly-Key'] = api_key
        for path in paths:
            url = urljoin('https://www.python.org', path)
            session.request('PURGE', url)
