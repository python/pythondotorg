"""Middleware that serves CMS pages as a fallback for 404 responses."""

import contextlib
from http import HTTPStatus

from django import http
from django.conf import settings

from .models import Page
from .views import PageView


class PageFallbackMiddleware:
    """Middleware that attempts to serve a CMS page when no other view matches."""

    def __init__(self, get_response):
        """Initialize with the next middleware or view in the chain."""
        self.get_response = get_response

    def get_queryset(self, request):
        """Return all pages for staff, published pages for everyone else."""
        if request.user.is_staff:
            return Page.objects.all()
        return Page.objects.published()

    def __call__(self, request):
        """Serve a CMS page if the normal response is a 404."""
        response = self.get_response(request)
        # No need to check for a page for non-404 responses.
        if response.status_code != HTTPStatus.NOT_FOUND:
            return response

        full_path = request.path[1:]

        page = None
        qs = self.get_queryset(request)

        try:
            page = qs.get(path=full_path)
        except Page.DoesNotExist:
            has_slash = full_path.endswith("/")
            full_path = full_path[:-1] if has_slash else full_path + "/"
            with contextlib.suppress(Page.DoesNotExist):
                page = qs.get(path=full_path)
        if settings.APPEND_SLASH and page is not None and not request.path.endswith("/"):
            scheme = "https" if request.is_secure() else "http"
            new_path = request.path + "/"
            new_url = f"{scheme}://{request.get_host()}{new_path}"
            return http.HttpResponsePermanentRedirect(new_url)
        if page is not None:
            response = PageView.as_view()(request, path=full_path)
            if hasattr(response, "render"):
                response.render()

        # No page was found. Return the response.
        return response
