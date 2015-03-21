from django.conf import settings
from django.db import models
from django.template.defaultfilters import truncatechars, striptags
from markupfield.fields import MarkupField

from cms.models import ContentManageable

from .managers import CodeSampleQuerySet


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'html')


class CodeSample(ContentManageable):
    code = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, blank=True)
    copy = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, blank=True)
    is_published = models.BooleanField(default=False, db_index=True)

    objects = CodeSampleQuerySet.as_manager()

    class Meta:
        verbose_name = 'sample'
        verbose_name_plural = 'samples'

    def __str__(self):
        return truncatechars(striptags(self.copy), 20)
