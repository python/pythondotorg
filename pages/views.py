"""Views for rendering CMS pages."""

import re

from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.views.generic import DetailView

from downloads.models import Release
from pages.models import Page


class PageView(DetailView):
    """Detail view for rendering a CMS page by its URL path."""

    template_name = "pages/default.html"
    template_name_field = "template_name"
    context_object_name = "page"

    # Use "path" as the lookup key, rather than the default "slug".
    slug_url_kwarg = "path"
    slug_field = "path"

    def get_template_names(self):
        """Use the template defined in the model or a default."""
        names = [self.template_name]

        if self.object and self.template_name_field:
            name = getattr(self.object, self.template_name_field, None)
            if name:
                names.insert(0, name)

        return names

    def get_queryset(self):
        """Return all pages for staff, published pages for everyone else."""
        if self.request.user.is_staff:
            return Page.objects.all()
        return Page.objects.published()

    @property
    def content_type(self):
        """Return the content type of the page for HTTP response headers."""
        return self.object.content_type

    def get_context_data(self, **kwargs):
        """Add pages app flag to the template context."""
        context = super().get_context_data(**kwargs)
        context["in_pages_app"] = True
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET requests, redirecting legacy download URLs when appropriate."""
        # Redirect '/download/releases/X.Y.Z' to
        # '/downloads/release/python-XYZ/' if the latter URL doesn't have
        # 'release_page' (which points to the former URL) field set.
        # See #956 for details.
        matched = re.match(r"/download/releases/([\d.]+)/$", self.request.path)
        if matched is not None:
            release_slug = "python-{}".format(matched.group(1).replace(".", ""))
            try:
                Release.objects.get(slug=release_slug, release_page__isnull=True)
            except Release.DoesNotExist:
                pass
            else:
                return HttpResponsePermanentRedirect(
                    reverse(
                        "download:download_release_detail",
                        kwargs={"release_slug": release_slug},
                    )
                )
        return super().get(request, *args, **kwargs)
