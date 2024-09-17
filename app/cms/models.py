"""
This is not the content management system you are looking for.

There aren't actually any "content" objects here (but do see the pages and boxes
apps) Instead, we treat content management as a set of attributes, and actions
around common "content management" tasks. These common attributes are:

    - automatic creation and updating dates
    - automatic tracking of a creator
    - access controls (TODO)
"""

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


class ContentManageable(models.Model):
    created = models.DateTimeField(default=timezone.now, blank=True, db_index=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)

    # We allow creator to be null=True so that we can, if we must, create a
    # ContentManageable object in a context where we don't have a creator (i.e.
    # where there isn't a request.user sitting around).
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(app_label)s_%(class)s_creator',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(app_label)s_%(class)s_modified',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    def save(self, **kwargs):
        self.updated = timezone.now()
        return super().save(**kwargs)

    class Meta:
        abstract = True


class NameSlugModel(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)
