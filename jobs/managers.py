from django.db.models import Manager
from django.db.models.query import QuerySet


class JobQuerySet(QuerySet):

    def approved(self):
        return self.filter(status__exact=self.model.STATUS_APPROVED)

    def archived(self):
        return self.filter(status__exact=self.model.STATUS_ARCHIVED)

    def draft(self):
        return self.filter(status__exact=self.model.STATUS_DRAFT)

    def expired(self):
        return self.filter(status__exact=self.model.STATUS_EXPIRED)

    def rejected(self):
        return self.filter(status__exact=self.model.STATUS_REJECTED)

    def removed(self):
        return self.filter(status__exact=self.model.STATUS_REMOVED)

    def review(self):
        return self.filter(status__exact=self.model.STATUS_REVIEW)


class JobManager(Manager):
    def get_query_set(self):
        return JobQuerySet(self.model, using=self._db)

    def approved(self):
        return self.get_query_set().approved()

    def archived(self):
        return self.get_query_set().archived()

    def draft(self):
        return self.get_query_set().draft()

    def rejected(self):
        return self.get_query_set().rejected()

    def removed(self):
        return self.get_query_set().removed()

    def review(self):
        return self.get_query_set().review()
