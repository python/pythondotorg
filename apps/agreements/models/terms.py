"""Published terms and their immutable versions."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.agreements.documents import sha256
from apps.agreements.orders.catalog import Catalog

# Documents are rendered on staging and locally too; they must always cite production.
CANONICAL_ORIGIN = "https://www.python.org"


class Terms(models.Model):
    """Standing terms with explicit publication and immutable document versions."""

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    is_public = models.BooleanField(
        default=False,
        help_text="Make published versions readable by everyone. Otherwise only staff and the parties may read them.",
    )
    under_review = models.BooleanField(
        default=False, help_text="Mark the terms as a draft for attorney review wherever they appear."
    )
    draft_markdown = models.TextField(blank=True, help_text="Working copy; not public until published.")
    draft_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    draft_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Terms are listed by title."""

        ordering = ("title",)
        verbose_name_plural = "terms"

    def __str__(self) -> str:
        """Return the title."""
        return self.title

    def get_absolute_url(self) -> str:
        """Return the public page for the current version."""
        return reverse("agreements:terms", kwargs={"slug": self.slug})

    def validate_is_public(self, is_public: bool) -> None:
        """Keep terms readable while any public program cites their slug."""
        if is_public or self.pk is None:
            return
        from apps.agreements.models.orders import Program

        for definition in Program.objects.filter(is_public=True).values_list("definition", flat=True):
            catalog = Catalog(definition)
            if any(item.terms_slug == self.slug for item in catalog.agreements.values()):
                message = "Make every program that cites these terms private before making the terms private."
                raise ValidationError(message)

    def clean(self) -> None:
        """Validate publication settings in model forms, including the admin."""
        super().clean()
        try:
            self.validate_is_public(self.is_public)
        except ValidationError as exc:
            raise ValidationError({"is_public": exc.messages}) from exc

    @cached_property
    def current_version(self) -> TermsVersion | None:
        """Return the version documents offered now cite."""
        return self.versions.order_by("-published_at", "-pk").first()


class TermsVersion(models.Model):
    """One published version of terms. It never changes: signed documents cite it."""

    terms = models.ForeignKey(Terms, on_delete=models.PROTECT, related_name="versions")
    version = models.SlugField(max_length=64)
    markdown = models.TextField()
    sha256 = models.CharField(max_length=64, editable=False)
    notes = models.TextField(blank=True, help_text="What changed from the previous version.")
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        """Newest first; a version label is used once per terms."""

        ordering = ("-published_at", "-pk")
        constraints = (models.UniqueConstraint(fields=("terms", "version"), name="one_terms_version_per_label"),)

    def __str__(self) -> str:
        """Return the terms and version."""
        return f"{self.terms.title}, version {self.version}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Hash the text on publication and refuse any later change."""
        if self.pk:
            msg = "A published terms version never changes; publish a new version instead."
            raise ValueError(msg)
        self.sha256 = sha256(self.markdown)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        """Return the permanent page for this version."""
        return reverse("agreements:terms_version", kwargs={"slug": self.terms.slug, "version": self.version})

    @property
    def permanent_url(self) -> str:
        """Absolute, permanent address that documents cite."""
        return CANONICAL_ORIGIN + self.get_absolute_url()
