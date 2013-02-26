from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.template.defaultfilters import slugify

import datetime

from cms.models import ContentManageable, NameSlugModel


# Create your models here.
class JobType(NameSlugModel):
    pass


class JobCategory(NameSlugModel):
    pass


class Company(NameSlugModel):
    pass


class Job(ContentManageable):
    NEW_THRESHOLD = datetime.timedelta(days=30)

    category = models.ForeignKey(JobCategory)
    job_types = models.ManyToManyField(JobType)
    company = models.ForeignKey(Company)

    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    location_slug = models.SlugField(max_length=350, editable=False)

    description = models.TextField()

    class Meta:
        ordering = ('-created',)

    def save(self, **kwargs):
        self.location_slug = slugify('%s %s %s' % (self.city, self.region, self.country))
        return super().save(**kwargs)

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.pk})

    @property
    def is_new(self):
        return self.created > (timezone.now() - self.NEW_THRESHOLD)
