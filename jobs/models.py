import datetime

from django.conf import settings
from django.urls import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils import timezone

from markupfield.fields import MarkupField

from cms.models import ContentManageable, NameSlugModel
from fastly.utils import purge_url

from .managers import JobQuerySet, JobTypeQuerySet, JobCategoryQuerySet
from .signals import (
    job_was_submitted, job_was_approved, job_was_rejected, comment_was_posted
)


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class JobType(NameSlugModel):
    active = models.BooleanField(default=True)

    objects = JobTypeQuerySet.as_manager()

    class Meta:
        verbose_name = 'job technologies'
        verbose_name_plural = 'job technologies'
        ordering = ('name', )


class JobCategory(NameSlugModel):
    active = models.BooleanField(default=True)

    objects = JobCategoryQuerySet.as_manager()

    class Meta:
        verbose_name = 'job category'
        verbose_name_plural = 'job categories'
        ordering = ('name', )


class Job(ContentManageable):
    NEW_THRESHOLD = datetime.timedelta(days=30)

    category = models.ForeignKey(
        JobCategory,
        related_name='jobs',
        limit_choices_to={'active': True},
        on_delete=models.CASCADE,
    )
    job_types = models.ManyToManyField(
        JobType,
        related_name='jobs',
        blank=True,
        verbose_name='Job technologies',
        limit_choices_to={'active': True},
    )
    other_job_type = models.CharField(
        verbose_name='Other job technologies',
        max_length=100,
        blank=True,
    )
    company_name = models.CharField(
        max_length=100,
        null=True)
    company_description = MarkupField(
        blank=True,
        default_markup_type=DEFAULT_MARKUP_TYPE)
    job_title = models.CharField(
        max_length=100)

    city = models.CharField(
        max_length=100)
    region = models.CharField(
        verbose_name='State, Province or Region',
        blank=True,
        max_length=100)
    country = models.CharField(
        max_length=100,
        db_index=True)
    location_slug = models.SlugField(
        max_length=350,
        editable=False)
    country_slug = models.SlugField(
        max_length=100,
        editable=False)

    description = MarkupField(
        verbose_name='Job description',
        default_markup_type=DEFAULT_MARKUP_TYPE)
    requirements = MarkupField(
        verbose_name='Job requirements',
        default_markup_type=DEFAULT_MARKUP_TYPE)

    contact = models.CharField(
        verbose_name='Contact name',
        null=True,
        blank=True,
        max_length=100)
    email = models.EmailField(
        verbose_name='Contact email')
    url = models.URLField(
        verbose_name='URL',
        null=True,
        blank=True)

    STATUS_DRAFT = 'draft'
    STATUS_REVIEW = 'review'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_ARCHIVED = 'archived'
    STATUS_REMOVED = 'removed'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = (
        (STATUS_DRAFT, 'draft'),
        (STATUS_REVIEW, 'review'),
        (STATUS_APPROVED, 'approved'),
        (STATUS_REJECTED, 'rejected'),
        (STATUS_ARCHIVED, 'archived'),
        (STATUS_REMOVED, 'removed'),
        (STATUS_EXPIRED, 'expired'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REVIEW,
        db_index=True)
    expires = models.DateTimeField(
        verbose_name='Job Listing Expiration Date',
        blank=True,
        null=True)

    telecommuting = models.BooleanField(
        verbose_name='Telecommuting allowed?',
        default=False)
    agencies = models.BooleanField(
        verbose_name='Agencies are OK to contact?',
        default=True)

    is_featured = models.BooleanField(default=False, db_index=True)

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'
        verbose_name = 'job'
        verbose_name_plural = 'jobs'
        permissions = [('can_moderate_jobs', 'Can moderate Job listings')]

    def __str__(self):
        return 'Job Listing #{}'.format(self.pk)

    def save(self, **kwargs):
        location_parts = (self.city, self.region, self.country)
        location_str = ''
        for location_part in location_parts:
            if location_part is not None:
                location_str = ' '.join([location_str, location_part])
        self.location_slug = slugify(location_str)
        self.country_slug = slugify(self.country)

        if not self.expires and self.status == self.STATUS_APPROVED:
            delta = datetime.timedelta(days=settings.JOB_THRESHOLD_DAYS)
            self.expires = timezone.now() + delta

        return super().save(**kwargs)

    def review(self):
        """Updates job status to Job.STATUS_REVIEW after preview was done by
        user.
        """
        old_status = self.status
        self.status = Job.STATUS_REVIEW
        self.save()
        if old_status != self.status:
            job_was_submitted.send(sender=self.__class__, job=self)

    def approve(self, approving_user):
        """Updates job status to Job.STATUS_APPROVED after approval was issued
        by approving_user.
        """
        self.status = Job.STATUS_APPROVED
        self.save()
        job_was_approved.send(sender=self.__class__, job=self,
                              approving_user=approving_user)

    def reject(self, rejecting_user):
        """Updates job status to Job.STATUS_REJECTED after rejection was issued
        by rejecing_user.
        """
        self.status = Job.STATUS_REJECTED
        self.save()
        job_was_rejected.send(sender=self.__class__, job=self,
                              rejecting_user=rejecting_user)

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.pk})

    @property
    def display_name(self):
        return "%s, %s" % (self.job_title, self.company_name)

    @property
    def display_description(self):
        return self.company_description

    @property
    def display_location(self):
        location_parts = [part for part in (self.city, self.region, self.country)
                            if part]
        location_str = ', '.join(location_parts)
        return location_str

    @property
    def is_new(self):
        return self.created > (timezone.now() - self.NEW_THRESHOLD)

    @property
    def editable(self):
        return self.status in (
            self.STATUS_DRAFT,
            self.STATUS_REVIEW,
            self.STATUS_REJECTED
        )

    def get_previous_listing(self):
        return self.get_previous_by_created(status=self.STATUS_APPROVED)

    def get_next_listing(self):
        return self.get_next_by_created(status=self.STATUS_APPROVED)


class JobReviewComment(ContentManageable):
    job = models.ForeignKey(Job, related_name='review_comments', on_delete=models.CASCADE)
    comment = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)

    class Meta:
        ordering = ('created',)

    def save(self, **kwargs):
        comment_was_posted.send(sender=self.__class__, comment=self)
        return super().save(**kwargs)

    def __str__(self):
        return '<Job #{}: {}>'.format(self.job.pk, self.comment.raw[:50])


@receiver(post_save, sender=Job)
def purge_fastly_cache(sender, instance, **kwargs):
    """
    Purge fastly.com cache on new jobs
    Requires settings.FASTLY_API_KEY being set
    """
    # Skip in fixtures
    if kwargs.get('raw', False):
        return

    if instance.status == Job.STATUS_APPROVED:
        purge_url(reverse('jobs:job_detail', kwargs={'pk': instance.pk}))
        purge_url(reverse('jobs:job_list'))
        purge_url(reverse('jobs:job_rss'))
