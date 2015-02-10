from django.db.models import Manager
from django.db.models.query import QuerySet


class PageQuerySet(QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def draft(self):
        return self.filter(is_published=False)


class PageManager(Manager):
    def get_queryset(self):
        return PageQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def draft(self):
        return self.get_queryset().draft()
