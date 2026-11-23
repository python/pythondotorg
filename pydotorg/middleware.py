"""Middleware for cache control and surrogate keys."""

import re

from django.conf import settings

SECTION_KEY_RE = re.compile(r"[A-Za-z0-9._-]+")


class AdminNoCaching:
    """Middleware to ensure the admin is not cached by Fastly or other caches."""

    def __init__(self, get_response):
        """Store the get_response callable."""
        self.get_response = get_response

    def __call__(self, request):
        """Set Cache-Control to private for admin requests."""
        response = self.get_response(request)
        if request.path.startswith("/admin"):
            response["Cache-Control"] = "private"
        return response


class GlobalSurrogateKey:
    """Middleware to insert a Surrogate-Key for purging in Fastly or other caches.

    Adds both a global key (for full site purges) and section-based keys
    derived from the URL path (for targeted purges like /downloads/).
    """

    def __init__(self, get_response):
        """Store the get_response callable."""
        self.get_response = get_response

    def get_section_key(self, path):
        """Extract section surrogate key from URL path.

        The first segment is only used when it is a plain name (letters, digits,
        ".", "_", "-"), so the key is always a single valid header token.

        Examples:
            /downloads/ -> downloads
            /downloads/release/python-3141/ -> downloads
            /events/python-events/ -> events
            / -> None
            /downloads. 3/ -> None

        """
        section = path.strip("/").split("/")[0]
        if SECTION_KEY_RE.fullmatch(section):
            return section
        return None

    def __call__(self, request):
        """Append the global and section surrogate keys to the response header."""
        response = self.get_response(request)
        keys = []
        if hasattr(settings, "GLOBAL_SURROGATE_KEY"):
            keys.append(settings.GLOBAL_SURROGATE_KEY)

        section_key = self.get_section_key(request.path)
        if section_key:
            keys.append(section_key)

        existing = response.get("Surrogate-Key")
        if existing:
            keys.append(existing)

        if keys:
            response["Surrogate-Key"] = " ".join(keys)

        return response
