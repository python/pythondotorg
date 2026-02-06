"""Models for the companies app."""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from markupfield.fields import MarkupField

from cms.models import NameSlugModel

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class Company(NameSlugModel):
    """A company that uses Python, displayed in the company directory."""

    about = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE)
    contact = models.CharField(blank=True, max_length=100)
    email = models.EmailField(blank=True)
    url = models.URLField("URL", blank=True)
    logo = models.ImageField(upload_to="companies/logos/", blank=True, null=True)

    class Meta:
        """Meta configuration for Company."""

        verbose_name = _("company")
        verbose_name_plural = _("companies")
        ordering = ("name",)
