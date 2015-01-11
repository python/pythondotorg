from django.views.generic import DetailView

from .models import Page


class PageView(DetailView):
    template_name = 'pages/default.html'
    template_name_field = 'template_name'
    context_object_name = 'page'

    # Use "path" as the lookup key, rather than the default "slug".
    slug_url_kwarg = 'path'
    slug_field = 'path'

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
