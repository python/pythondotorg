class AdminNoCaching:
    """
    Middleware to ensure the admin is not cached by Fastly or other caches
    """

    def process_response(self, request, response):
        if request.path.startswith('/admin'):
            response['Cache-Control'] = 'private'
        return response
