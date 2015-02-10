from django.db.models import Manager
from django.db.models.query import QuerySet


class SponsorQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)

    def featured(self):
        return self.published().filter(featured=True)


class SponsorManager(Manager):
    def get_queryset(self):
        return SponsorQuerySet(self.model, using=self._db)

    def draft(self):
        return self.get_queryset().draft()

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()
