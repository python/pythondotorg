"""Middleware for cache control and surrogate keys."""

from django.conf import settings


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

    def _get_section_key(self, path):
        """Extract section surrogate key from URL path.

        Examples:
            /downloads/ -> downloads
            /downloads/release/python-3141/ -> downloads
            /events/python-events/ -> events
            / -> None
        """
        parts = path.strip("/").split("/")
        if parts and parts[0]:
            return parts[0]
        return None

    def __call__(self, request):
        """Append the global and section surrogate keys to the response header."""
        response = self.get_response(request)
        keys = []
        if hasattr(settings, "GLOBAL_SURROGATE_KEY"):
            keys.append(settings.GLOBAL_SURROGATE_KEY)

        section_key = self._get_section_key(request.path)
        if section_key:
            keys.append(section_key)

        existing = response.get("Surrogate-Key")
        if existing:
            keys.append(existing)

        if keys:
            response["Surrogate-Key"] = " ".join(keys)

        return response
