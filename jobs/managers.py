import datetime

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


class JobQuerySet(QuerySet):

    def approved(self):
        return self.filter(status=self.model.STATUS_APPROVED)

    def archived(self):
        return self.filter(status=self.model.STATUS_ARCHIVED)

    def draft(self):
        return self.filter(status=self.model.STATUS_DRAFT)

    def expired(self):
        return self.filter(status=self.model.STATUS_EXPIRED)

    def rejected(self):
        return self.filter(status=self.model.STATUS_REJECTED)

    def removed(self):
        return self.filter(status=self.model.STATUS_REMOVED)

    def featured(self):
        return self.filter(is_featured=True)

    def editable(self):
        return self.exclude(status=self.model.STATUS_APPROVED)

    def review(self):
        review_threshold = timezone.now() - datetime.timedelta(days=120)
        return self.filter(
            status=self.model.STATUS_REVIEW,
            created__gte=review_threshold,
        ).order_by('created')

    def moderate(self):
        return self.exclude(status=self.model.STATUS_REVIEW)

    def visible(self):
        """
        Jobs that should be publicly visible on the website. They will have an
        approved status and be less than 90 days old
        """
        return self.approved().filter(expires__gte=timezone.now())

    def by(self, user):
        return self.filter(creator=user)
