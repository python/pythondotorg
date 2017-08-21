from django.views.generic import TemplateView

from .models import BlogEntry, Translation, Contributor


class BlogHome(TemplateView):
    """ Main blog view """
    template_name = 'blogs/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        entries = BlogEntry.objects.order_by('-pub_date')[:6]
        latest_entry = None
        other_entries = []

        if entries:
            latest_entry = entries[0]
            other_entries = entries[1:]

        context.update({
            'latest_entry': latest_entry,
            'entries': other_entries,
            'translations': Translation.objects.all(),
            'contributors': Contributor.objects.all(),
        })

        return context
