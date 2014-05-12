import datetime

from django.conf import settings
from django.contrib.comments.signals import comment_was_posted
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from markupfield.fields import MarkupField

from .managers import JobManager
from .listeners import (on_comment_was_posted, on_job_was_approved,
                        on_job_was_rejected)
from .signals import job_was_approved, job_was_rejected
from cms.models import ContentManageable, NameSlugModel


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class JobType(NameSlugModel):

    class Meta(object):
        verbose_name = 'job type'
        verbose_name_plural = 'job types'
        ordering = ('name', )


class JobCategory(NameSlugModel):

    class Meta(object):
        verbose_name = 'job category'
        verbose_name_plural = 'job categories'
        ordering = ('name', )


class Job(ContentManageable):
    NEW_THRESHOLD = datetime.timedelta(days=30)

    category = models.ForeignKey(JobCategory, related_name='jobs')
    job_types = models.ManyToManyField(JobType, related_name='jobs', blank=True)
    company = models.ForeignKey('companies.Company', related_name='jobs', blank=True, null=True)

    company_name = models.CharField(max_length=100, blank=True, null=True)
    company_description = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE)
    job_title = models.CharField(blank=True, null=True, max_length=100)

    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100, db_index=True)
    location_slug = models.SlugField(max_length=350, editable=False)
    country_slug = models.SlugField(max_length=100, editable=False)

    description = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE)
    requirements = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE)

    contact = models.CharField(null=True, blank=True, max_length=100)
    email = models.EmailField()
    url = models.URLField('URL', null=True, blank=True)

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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_REVIEW, db_index=True)
    dt_start = models.DateTimeField('Job start date', blank=True, null=True)
    dt_end = models.DateTimeField('Job end date', blank=True, null=True)

    telecommuting = models.BooleanField(default=False)
    agencies = models.BooleanField(default=True)

    is_featured = models.BooleanField(default=False, db_index=True)

    objects = JobManager()

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'
        verbose_name = 'job'
        verbose_name_plural = 'jobs'
        permissions = [('can_moderate_jobs', 'Can moderate Job listings')]

    def __str__(self):
        return 'Job Listing #{0}'.format(self.pk)

    def save(self, **kwargs):
        self.location_slug = slugify('%s %s %s' % (self.city, self.region, self.country))
        self.country_slug = slugify(self.country)

        if not self.dt_start and self.status == self.STATUS_APPROVED:
            self.dt_start = timezone.now()
            self.dt_end = timezone.now() + self.NEW_THRESHOLD

        return super().save(**kwargs)

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
        return self.company_name or getattr(self.company, 'name', '')

    @property
    def display_description(self):
        if self.company_description.raw.strip():
            return self.company_description
        return getattr(self.company, 'about', '')

    @property
    def is_new(self):
        return self.created > (timezone.now() - self.NEW_THRESHOLD)

    @property
    def editable(self):
        return self.status in (self.STATUS_DRAFT, self.STATUS_REVIEW,
            self.STATUS_REJECTED)

comment_was_posted.connect(on_comment_was_posted)
job_was_approved.connect(on_job_was_approved)
job_was_rejected.connect(on_job_was_rejected)
