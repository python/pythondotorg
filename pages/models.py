"""
Simple "flat pages".

These get used for the static (non-automated) large chunks of content. Notice
that pages don't have any actual notion of where they live; instead, they're
positioned into the URL structure using the nav app.
"""

from django.db import models
from cms.models import ContentManageable
from .managers import PageManager

class Page(ContentManageable):
    title = models.CharField(max_length=500)
    content = models.TextField()
    is_published = models.BooleanField(default=True)

    objects = PageManager()

    def __str__(self):
        return self.title
