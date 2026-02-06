"""Custom querysets for the pages app."""

from django.db.models.query import QuerySet


class PageQuerySet(QuerySet):
    """Custom queryset providing filtering by page publication status."""

    def published(self):
        """Return only published pages."""
        return self.filter(is_published=True)

    def draft(self):
        """Return only unpublished draft pages."""
        return self.filter(is_published=False)
