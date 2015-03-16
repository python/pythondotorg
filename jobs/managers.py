from django.db.models import Manager
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import timezone


class JobTypeQuerySet(QuerySet):

    def active(self):
        """ active Job Types """
        return self.filter(active=True)

    def with_active_jobs(self):
        """ JobTypes with active jobs """
        now = timezone.now()
        return self.active().filter(
            jobs__status='approved',
            jobs__expires__gte=now,
        ).distinct()


class JobTypeManager(Manager):
    """ Job Type Manager """

    def get_queryset(self):
        return JobTypeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_active_jobs(self):
        """ Return all JobTypes that have active Jobs """
        return self.get_queryset().with_active_jobs()


class JobCategoryQuerySet(QuerySet):

    def active(self):
        return self.filter(active=True)

    def with_active_jobs(self):
        """ JobCategory with active jobs """
        now = timezone.now()
        return self.filter(
            jobs__status='approved',
            jobs__expires__gte=now,
        ).distinct()


class JobCategoryManager(Manager):
    """ JobCategory Manager """

    def get_queryset(self):
        return JobCategoryQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def with_active_jobs(self):
        """ Return all JobCategories that have active Jobs """
        return self.get_queryset().with_active_jobs()


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

    def visible(self):
        """
        Jobs that should be publicly visible on the website. They will have an
        approved status and be less than 90 days old
        """
        now = timezone.now()
        return self.filter(
            Q(status__exact=self.model.STATUS_APPROVED) &
            Q(expires__gte=now)
        )


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

    def visible(self):
        return self.get_queryset().visible()
