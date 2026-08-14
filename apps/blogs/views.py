"""Views for the blogs app."""

from django.views.generic import TemplateView

from apps.blogs.models import BlogEntry

# Number of entries the page shows. The newest one goes in the page
# header, the rest go in the "Latest News" list.
ENTRY_LIST_LIMIT = 10


class BlogHome(TemplateView):
    """Main blog view."""

    template_name = "blogs/index.html"

    def get_context_data(self, **kwargs):
        """Return the latest blog entries for the blog homepage."""
        context = super().get_context_data(**kwargs)

        entries = BlogEntry.objects.order_by("-pub_date")[:ENTRY_LIST_LIMIT]
        latest_entry = None
        other_entries = []

        if entries:
            latest_entry = entries[0]
            other_entries = entries[1:]

        context.update(
            {
                "latest_entry": latest_entry,
                "entries": other_entries,
            }
        )

        return context
