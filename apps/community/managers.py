"""Custom querysets for the community app."""

from django.db.models.query import QuerySet


class PostQuerySet(QuerySet):
    """Custom queryset providing filtering by post visibility status."""

    def public(self):
        """Return only publicly visible posts."""
        return self.filter(status__exact=self.model.STATUS_PUBLIC)

    def private(self):
        """Return only private posts."""
        return self.filter(
            status__in=[
                self.model.STATUS_PRIVATE,
            ]
        )
