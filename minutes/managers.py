from django.db.models import Manager
from django.db.models.query import QuerySet


class MinutesQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)


class MinutesManager(Manager):
    def get_queryset(self):
        return MinutesQuerySet(self.model, using=self._db)

    def draft(self):
        return self.get_queryset().draft()

    def published(self):
        return self.get_queryset().published()
