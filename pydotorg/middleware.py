class AdminNoCaching:
    """
    Middleware to ensure the admin is not cached by Fastly or other caches
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith('/admin'):
            response['Cache-Control'] = 'private'
        return response
