"""Models for PSF board meeting minutes."""

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from markupfield.fields import MarkupField

from apps.cms.models import ContentManageable
from apps.minutes.managers import MinutesQuerySet
from fastly.utils import purge_url

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class Minutes(ContentManageable):
    """A record of PSF board meeting minutes for a specific date."""

    date = models.DateField(verbose_name="Meeting Date", db_index=True)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False, db_index=True)

    objects = MinutesQuerySet.as_manager()

    class Meta:
        """Meta configuration for Minutes."""

        verbose_name = "minutes"
        verbose_name_plural = "minutes"

    def __str__(self):
        """Return a human-readable label with the meeting date."""
        return f"PSF Meeting Minutes {self.date.strftime('%B %d, %Y')}"

    def get_absolute_url(self):
        """Return the URL for the minutes detail page."""
        return reverse(
            "minutes_detail",
            kwargs={
                "year": self.get_date_year(),
                "month": self.get_date_month(),
                "day": self.get_date_day(),
            },
        )

    # Helper methods for sitetree
    def get_date_year(self):
        """Return the meeting date's four-digit year string."""
        return self.date.strftime("%Y")

    def get_date_month(self):
        """Return the meeting date's zero-padded month string."""
        return self.date.strftime("%m").zfill(2)

    def get_date_day(self):
        """Return the meeting date's zero-padded day string."""
        return self.date.strftime("%d").zfill(2)


@receiver(pre_save, sender=Minutes)
def remember_previous_url(sender, instance, **kwargs):
    """Remember the stored detail URL so a changed meeting date also purges the old page."""
    instance.previous_url = None
    if kwargs.get("raw", False) or instance.pk is None:
        return
    previous = Minutes.objects.filter(pk=instance.pk).only("date").first()
    if previous is not None:
        instance.previous_url = previous.get_absolute_url()


@receiver(post_save, sender=Minutes)
@receiver(post_delete, sender=Minutes)
def purge_fastly_cache(sender, instance, **kwargs):
    """Purge the minutes detail, list, and feed pages so edits show up immediately.

    Purges regardless of publish state so unpublished or deleted minutes disappear too.
    """
    # Skip in fixtures
    if kwargs.get("raw", False):
        return

    current_url = instance.get_absolute_url()
    purge_url(current_url)
    previous_url = getattr(instance, "previous_url", None)
    if previous_url and previous_url != current_url:
        purge_url(previous_url)
    purge_url(reverse("minutes_list"))
    purge_url(reverse("minutes_feed"))
