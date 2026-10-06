"""Published terms and their immutable versions."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property

from apps.agreements.documents import sha256

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

    def __str__(self):
        """Return the title."""
        return self.title

    def get_absolute_url(self):
        """Return the public page for the current version."""
        return reverse("agreements:terms", kwargs={"slug": self.slug})

    @cached_property
    def current_version(self):
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

    def __str__(self):
        """Return the terms and version."""
        return f"{self.terms.title}, version {self.version}"

    def save(self, *args, **kwargs):
        """Hash the text on publication and refuse any later change."""
        if self.pk:
            msg = "A published terms version never changes; publish a new version instead."
            raise ValueError(msg)
        self.sha256 = sha256(self.markdown)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the permanent page for this version."""
        return reverse("agreements:terms_version", kwargs={"slug": self.terms.slug, "version": self.version})

    @property
    def permanent_url(self):
        """Absolute, permanent address that documents cite."""
        return CANONICAL_ORIGIN + self.get_absolute_url()
