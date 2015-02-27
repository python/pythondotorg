from django.db.models import Manager
from django.db.models.query import QuerySet


class JobTypeQuerySet(QuerySet):
    def active_types(self):
        """ JobTypes with active jobs """
        return self.filter(jobs__status='approved').distinct()


class JobTypeManager(Manager):
    """ Job Type Manager """

    def get_queryset(self):
        return JobTypeQuerySet(self.model, using=self._db)

    def active_types(self):
        """ Return all JobTypes that have active Jobs """
        return self.get_queryset().active_types()


class JobCategoryQuerySet(QuerySet):
    def active_categories(self):
        """ JobCategory with active jobs """
        return self.filter(jobs__status='approved').distinct()


class JobCategoryManager(Manager):
    """ JobCategory Manager """

    def get_queryset(self):
        return JobCategoryQuerySet(self.model, using=self._db)

    def active_categories(self):
        """ Return all JobCategories that have active Jobs """
        return self.get_queryset().active_categories()


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
