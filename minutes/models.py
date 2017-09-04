from django.conf import settings
from django.urls import reverse
from django.db import models

from markupfield.fields import MarkupField

from cms.models import ContentManageable

from .managers import MinutesQuerySet

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class Minutes(ContentManageable):
    date = models.DateField(verbose_name='Meeting Date', db_index=True)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False, db_index=True)

    objects = MinutesQuerySet.as_manager()

    class Meta:
        verbose_name = 'minutes'
        verbose_name_plural = 'minutes'

    def __str__(self):
        return "PSF Meeting Minutes %s" % self.date.strftime("%B %d, %Y")

    def get_absolute_url(self):
        return reverse('minutes_detail', kwargs={
            'year': self.get_date_year(),
            'month': self.get_date_month(),
            'day': self.get_date_day(),
        })

    # Helper methods for sitetree
    def get_date_year(self):
        return self.date.strftime("%Y")

    def get_date_month(self):
        return self.date.strftime("%m").zfill(2)

    def get_date_day(self):
        return self.date.strftime("%d").zfill(2)
