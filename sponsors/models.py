from django.conf import settings
from django.db import models
from markupfield.fields import MarkupField

from cms.models import ContentManageable
from companies.models import Company

from .managers import SponsorQuerySet

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class Sponsor(ContentManageable):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, blank=True)
    is_published = models.BooleanField(default=False, db_index=True)
    featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Check to include Sponsor in feature rotation",
    )

    objects = SponsorQuerySet.as_manager()

    class Meta:
        verbose_name = 'sponsor'
        verbose_name_plural = 'sponsors'

    def __str__(self):
        return self.company.name
