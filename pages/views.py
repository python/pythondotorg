import re

from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.views.generic import DetailView

from downloads.models import Release
from .models import Page


class PageView(DetailView):
    template_name = 'pages/default.html'
    template_name_field = 'template_name'
    context_object_name = 'page'

    # Use "path" as the lookup key, rather than the default "slug".
    slug_url_kwarg = 'path'
    slug_field = 'path'

    def get_template_names(self):
        """ Use the template defined in the model or a default """
        names = [self.template_name]

        if self.object and self.template_name_field:
            name = getattr(self.object, self.template_name_field, None)
            if name:
                names.insert(0, name)

        return names

    def get_queryset(self):
        if self.request.user.is_staff:
            return Page.objects.all()
        else:
            return Page.objects.published()

    @property
    def content_type(self):
        return self.object.content_type

    def get_extra_context(self, *args, **kwargs):
        context = self.super().get_extra_context(*args, **kwargs)
        context['in_pages_app'] = True
        return context

    def get(self, request, *args, **kwargs):
        # Redirect '/download/releases/X.Y.Z' to
        # '/downloads/release/python-XYZ/' if the latter URL doesn't have
        # 'release_page' (which points to the former URL) field set.
        # See #956 for details.
        matched = re.match(r'/download/releases/([\d.]+)/$', self.request.path)
        if matched is not None:
            release_slug = 'python-{}'.format(matched.group(1).replace('.', ''))
            try:
                Release.objects.get(slug=release_slug, release_page__isnull=True)
            except Release.DoesNotExist:
                pass
            else:
                return HttpResponsePermanentRedirect(
                    reverse(
                        'download:download_release_detail',
                        kwargs={'release_slug': release_slug},
                    )
                )
        return super().get(request, *args, **kwargs)
