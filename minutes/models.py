from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from markupfield.fields import MarkupField

from .managers import MinutesManager
from cms.models import ContentManageable


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class Minutes(ContentManageable):
    date = models.DateField(verbose_name='Meeting Date', db_index=True)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False, db_index=True)

    objects = MinutesManager()

    class Meta:
        verbose_name = 'minutes'
        verbose_name_plural = 'minutes'

    def __str__(self):
        return "PSF Meeting Minutes %s" % self.date.strftime("%B %d, %Y")

    def get_absolute_url(self):
        return reverse('minutes_detail', kwargs={
            'year': self.date.strftime("%Y"),
            'month': self.date.strftime("%m").zfill(2),
            'day': self.date.strftime("%d").zfill(2),
        })
