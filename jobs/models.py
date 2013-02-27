from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.template.defaultfilters import slugify

import datetime

from markupfield.fields import MarkupField

from cms.models import ContentManageable, NameSlugModel

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


# Create your models here.
class JobType(NameSlugModel):
    pass


class JobCategory(NameSlugModel):
    pass


class Job(ContentManageable):
    NEW_THRESHOLD = datetime.timedelta(days=30)

    category = models.ForeignKey(JobCategory, related_name='jobs')
    job_types = models.ManyToManyField(JobType, related_name='jobs')
    company = models.ForeignKey('companies.Company', related_name='jobs')

    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    location_slug = models.SlugField(max_length=350, editable=False)

    description = models.TextField()
    requirements = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE)

    contact = models.CharField(null=True, blank=True, max_length=100)
    email = models.EmailField()
    url = models.URLField(null=True, blank=True)

    telecommuting = models.BooleanField(default=True)
    agencies = models.BooleanField(default=True)

    class Meta:
        ordering = ('-created',)
        get_latest_by = 'created'

    def save(self, **kwargs):
        self.location_slug = slugify('%s %s %s' % (self.city, self.region, self.country))
        return super().save(**kwargs)

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.pk})

    @property
    def is_new(self):
        return self.created > (timezone.now() - self.NEW_THRESHOLD)
