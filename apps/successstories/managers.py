"""Custom managers and querysets for the success stories app."""

import random

from django.db.models import Manager
from django.db.models.aggregates import Count
from django.db.models.query import QuerySet


class StoryQuerySet(QuerySet):
    """Custom queryset providing filtering by story publication and feature status."""

    def draft(self):
        """Return only unpublished draft stories."""
        return self.filter(is_published=False)

    def published(self):
        """Return only published stories."""
        return self.filter(is_published=True)

    def featured(self):
        """Return published stories that are marked as featured."""
        return self.published().filter(featured=True)

    def latest(self):
        """Return the four most recently published stories."""
        return self.published()[:4]


class StoryManager(Manager.from_queryset(StoryQuerySet)):
    """Manager adding random featured story selection to the StoryQuerySet."""

    def random_featured(self):
        """Return a single random featured story without using ORDER BY RANDOM."""
        # We don't just call queryset.order_by('?') because that
        # would kill the database.
        count = self.featured().aggregate(count=Count("id"))["count"]
        if count == 0:
            return self.get_queryset().none()
        random_index = random.randint(0, count - 1)  # noqa: S311 - not for security, random display selection
        return self.featured()[random_index]
