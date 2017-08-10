import random

from django.db.models import Manager
from django.db.models.query import QuerySet
from django.db.models.aggregates import Count


class StoryQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)

    def featured(self):
        return self.published().filter(featured=True)

    def latest(self):
        return self.published()[:4]


# TODO: Use StoryQuerySet.as_manager()
class StoryManager(Manager):
    def get_queryset(self):
        return StoryQuerySet(self.model, using=self._db)

    def draft(self):
        return self.get_queryset().draft()

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()

    def latest(self):
        return self.get_queryset().latest()

    def random_featured(self):
        # We don't just call queryset.order_by('?') because that
        # would kill the database.
        count = self.featured().aggregate(count=Count('id'))['count']
        if count == 0:
            return self.get_queryset().none()
        random_index = random.randint(0, count - 1)
        return self.featured()[random_index]
