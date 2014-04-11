from django.conf import settings
from .models import Page
from .views import PageView


class PageFallbackMiddleware(object):

    def get_queryset(self, request):
        if request.user.is_staff:
            return Page.objects.all()
        else:
            return Page.objects.published()

    def process_response(self, request, response):
        # No need to check for a page for non-404 responses.
        if response.status_code != 404:
            return response

        full_path = request.path[1:]

        page = None
        qs = self.get_queryset(request)

        try:
            page = qs.get(path=full_path)
        except Page.DoesNotExist:
            pass
        if settings.APPEND_SLASH and page is None:
            full_path = full_path.rstrip('/')
            try:
                page = qs.get(path=full_path)
            except Page.DoesNotExist:
                pass
        if page is not None:
            response = PageView.as_view()(request, path=full_path)
            if hasattr(response, 'render'):
                response.render()

        # No page was found. Return the response.
        return response
