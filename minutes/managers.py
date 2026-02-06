"""Custom querysets for the minutes app."""

from django.db.models.query import QuerySet


class MinutesQuerySet(QuerySet):
    """Custom queryset providing filtering by minutes publication status."""

    def draft(self):
        """Return only unpublished draft minutes."""
        return self.filter(is_published=False)

    def published(self):
        """Return only published minutes."""
        return self.filter(is_published=True)

    def latest(self):
        """Return published minutes ordered by most recent date first."""
        return self.published().order_by("-date")
