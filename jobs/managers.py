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

    def featured(self):
        return self.filter(is_featured=True)

    def review(self):
        return self.filter(status__in=[
            self.model.STATUS_REVIEW,
        ])


class JobManager(Manager):
    def get_queryset(self):
        return JobQuerySet(self.model, using=self._db)

    def approved(self):
        return self.get_queryset().approved()

    def archived(self):
        return self.get_queryset().archived()

    def draft(self):
        return self.get_queryset().draft()

    def expired(self):
        return self.get_queryset().expired()

    def rejected(self):
        return self.get_queryset().rejected()

    def removed(self):
        return self.get_queryset().removed()

    def featured(self):
        return self.get_queryset().featured()

    def review(self):
        return self.get_queryset().review()
