from django.db.models import Manager
from django.db.models.query import QuerySet


class PostQuerySet(QuerySet):

    def public(self):
        return self.filter(status__exact=self.model.STATUS_PUBLIC)

    def private(self):
        return self.filter(status__in=[
            self.model.STATUS_PRIVATE,
        ])


class PostManager(Manager):

    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def public(self):
        return self.get_queryset().public()

    def private(self):
        return self.get_queryset().private()
