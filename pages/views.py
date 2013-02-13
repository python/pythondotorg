from django.views.generic import DetailView
from .models import Page

class PageView(DetailView):
    # FIXME: probably should allow custom templates via template_name_field.
    template_name = 'python/inner.html'

    context_object_name = 'page'

    # Use "path" as the lookup key, rather than the default "slug".
    slug_url_kwarg = 'path'
    slug_field = 'path'

    def get_queryset(self):
        # FIXME: show draft pages to... certain people... once we define who.
        return Page.objects.published()
