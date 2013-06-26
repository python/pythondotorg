from django.db.models import Manager
from django.db.models.query import QuerySet


class PostQuerySet(QuerySet):

    def public(self):
        return self.filter(status__exact=self.model.STATUS_APPROVED)

    def review(self):
        return self.filter(status__in=[
            self.model.STATUS_REVIEW,
        ])


class PostManager(Manager):

    def get_query_set(self):
        return PostQuerySet(self.model, using=self._db)

    def public(self):
        return self.get_query_set().public()

    def review(self):
        return self.get_query_set().review()
