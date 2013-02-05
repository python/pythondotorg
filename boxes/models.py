"""
A "box" is a re-usable content snippet - footers, blurbs, etc.

These generally should be avoided in favor of the more simplistic "just put
content in a template", but in cases where a bit of content needs to be
admin-editable, use a Box.

These should also not be used for single pages, for that see the pages app.
"""

from django.db import models
from cms.models import ContentManageable

class Box(ContentManageable):
    label = models.SlugField(max_length=100, unique=True)
    content = models.TextField()

    def __str__(self):
        return self.label

    class Meta:
        verbose_name_plural = 'boxes'
