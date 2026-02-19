"""Utility functions for interacting with the Fastly CDN API."""

import requests
from django.conf import settings


def purge_url(path):
    """Purge a Fastly.com URL given a path. path argument must begin with a slash."""
    if settings.DEBUG:
        return None

    api_key = getattr(settings, "FASTLY_API_KEY", None)
    if api_key:
        return requests.request(
            "PURGE",
            f"https://www.python.org{path}",
            headers={"Fastly-Key": api_key},
            timeout=30,
        )

    return None


def purge_surrogate_key(key):
    """Purge all Fastly cached content tagged with a surrogate key.

    Common keys (set by GlobalSurrogateKey middleware):
        - 'pydotorg-app': Purges entire site
        - 'downloads': Purges all /downloads/* pages
        - 'events': Purges all /events/* pages
        - 'sponsors': Purges all /sponsors/* pages
        - etc. (first path segment becomes the surrogate key)

    Returns the response from Fastly API, or None if not configured.
    """
    if settings.DEBUG:
        return None

    api_key = getattr(settings, "FASTLY_API_KEY", None)
    service_id = getattr(settings, "FASTLY_SERVICE_ID", None)
    if not api_key or not service_id:
        return None

    return requests.post(
        f"https://api.fastly.com/service/{service_id}/purge/{key}",
        headers={"Fastly-Key": api_key},
        timeout=30,
    )
