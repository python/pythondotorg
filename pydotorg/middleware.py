from django.conf import settings


class AdminNoCaching:
    """
    Middleware to ensure the admin is not cached by Fastly or other caches
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/admin"):
            response["Cache-Control"] = "private"
        return response


class GlobalSurrogateKey:
    """
    Middleware to insert a Surrogate-Key for purging in Fastly or other caches
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(settings, "GLOBAL_SURROGATE_KEY"):
            response["Surrogate-Key"] = " ".join(
                filter(
                    None, [settings.GLOBAL_SURROGATE_KEY, response.get("Surrogate-Key")]
                )
            )
        return response
