"""Custom querysets for the codesamples app."""

from django.db.models.query import QuerySet


class CodeSampleQuerySet(QuerySet):
    """Custom queryset with filtering shortcuts for code samples."""

    def draft(self):
        """Return only unpublished code samples."""
        return self.filter(is_published=False)

    def published(self):
        """Return only published code samples."""
        return self.filter(is_published=True)
