"""Querysets for filtering jobs, job types, and job categories."""

import datetime

from django.db.models.query import QuerySet
from django.utils import timezone


class JobTypeQuerySet(QuerySet):
    """Custom queryset for filtering job types."""

    def active(self):
        """Active Job Types."""
        return self.filter(active=True)

    def with_active_jobs(self):
        """JobTypes with active jobs."""
        now = timezone.now()
        return (
            self.active()
            .filter(
                jobs__status="approved",
                jobs__expires__gte=now,
            )
            .distinct()
        )


class JobCategoryQuerySet(QuerySet):
    """Custom queryset for filtering job categories."""

    def active(self):
        """Return active job categories."""
        return self.filter(active=True)

    def with_active_jobs(self):
        """JobCategory with active jobs."""
        now = timezone.now()
        return self.filter(
            jobs__status="approved",
            jobs__expires__gte=now,
        ).distinct()


class JobQuerySet(QuerySet):
    """Custom queryset for filtering job listings."""

    def approved(self):
        """Return approved jobs."""
        return self.filter(status=self.model.STATUS_APPROVED)

    def archived(self):
        """Return archived jobs."""
        return self.filter(status=self.model.STATUS_ARCHIVED)

    def draft(self):
        """Return draft jobs."""
        return self.filter(status=self.model.STATUS_DRAFT)

    def expired(self):
        """Return expired jobs."""
        return self.filter(status=self.model.STATUS_EXPIRED)

    def rejected(self):
        """Return rejected jobs."""
        return self.filter(status=self.model.STATUS_REJECTED)

    def removed(self):
        """Return removed jobs."""
        return self.filter(status=self.model.STATUS_REMOVED)

    def featured(self):
        """Return featured jobs."""
        return self.filter(is_featured=True)

    def editable(self):
        """Return jobs that are not yet approved and can be edited."""
        return self.exclude(status=self.model.STATUS_APPROVED)

    def review(self):
        """Return jobs pending review, created within the last 120 days."""
        review_threshold = timezone.now() - datetime.timedelta(days=120)
        return self.filter(
            status=self.model.STATUS_REVIEW,
            created__gte=review_threshold,
        ).order_by("created")

    def moderate(self):
        """Return jobs that are not in review status (for moderation views)."""
        return self.exclude(status=self.model.STATUS_REVIEW)

    def visible(self):
        """Return jobs that should be publicly visible on the website.

        They will have an approved status and be less than 90 days old.
        """
        return self.approved().filter(expires__gte=timezone.now())

    def by(self, user):
        """Return jobs created by the given user."""
        return self.filter(creator=user)
