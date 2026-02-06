"""Content management attributes and mixins (not a full CMS).

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
    """Abstract mixin providing created/updated timestamps and creator tracking."""

    created = models.DateTimeField(default=timezone.now, blank=True, db_index=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)

    # We allow creator to be null=True so that we can, if we must, create a
    # ContentManageable object in a context where we don't have a creator (i.e.
    # where there isn't a request.user sitting around).
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(app_label)s_%(class)s_creator",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="%(app_label)s_%(class)s_modified",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        """Meta configuration for ContentManageable."""

        abstract = True

    def save(self, **kwargs):
        """Update the 'updated' timestamp before saving."""
        self.updated = timezone.now()
        return super().save(**kwargs)


class NameSlugModel(models.Model):
    """Abstract model providing a name and auto-generated slug."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        """Meta configuration for NameSlugModel."""

        abstract = True

    def __str__(self):
        """Return the model name."""
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not already set."""
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)
