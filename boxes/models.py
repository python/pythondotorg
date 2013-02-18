"""
A "box" is a re-usable content snippet - footers, blurbs, etc.

These generally should be avoided in favor of the more simplistic "just put
content in a template", but in cases where a bit of content needs to be
admin-editable, use a Box.

These should also not be used for single pages, for that see the pages app.
"""

from django.conf import settings
from django.db import models
from markupfield.fields import MarkupField
from cms.models import ContentManageable

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')

class Box(ContentManageable):
    label = models.SlugField(max_length=100, unique=True)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)

    def __str__(self):
        return self.label

    class Meta:
        verbose_name_plural = 'boxes'
