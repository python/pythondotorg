from django.conf import settings
from django.db import models
from markupfield.fields import MarkupField

from .managers import SponsorManager
from cms.models import ContentManageable
from companies.models import Company


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class Sponsor(ContentManageable):
    company = models.ForeignKey(Company)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, blank=True)
    is_published = models.BooleanField(default=False)

    objects = SponsorManager()

    class Meta:
        verbose_name = 'sponsor'
        verbose_name_plural = 'sponsors'

    def __str__(self):
        return self.company.name
