"""Models for Python releases, release files, and operating systems."""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from markupfield.fields import MarkupField

from apps.boxes.models import Box
from apps.cms.models import ContentManageable, NameSlugModel
from apps.downloads.managers import ReleaseManager
from apps.pages.models import Page
from fastly.utils import purge_surrogate_key, purge_url

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "markdown")


class OS(ContentManageable, NameSlugModel):
    """OS for Python release."""

    class Meta:
        """Meta configuration for OS."""

        verbose_name = "Operating System"
        verbose_name_plural = "Operating Systems"
        ordering = ("name",)

    def __str__(self):
        """Return string representation."""
        return self.name

    def get_absolute_url(self):
        """Return the URL for this OS's download list page."""
        return reverse("download:download_os_list", kwargs={"os_slug": self.slug})


class Release(ContentManageable, NameSlugModel):
    """A particular version release.

    Name field should be version number for example: 3.3.4 or 2.7.6.
    """

    PYTHON1 = 1
    PYTHON2 = 2
    PYTHON3 = 3
    PYMANAGER = 100
    PYTHON_VERSION_CHOICES = (
        (PYTHON3, "Python 3.x.x"),
        (PYTHON2, "Python 2.x.x"),
        (PYTHON1, "Python 1.x.x"),
        (PYMANAGER, "Python install manager"),
    )
    version = models.IntegerField(default=PYTHON3, choices=PYTHON_VERSION_CHOICES)
    is_latest = models.BooleanField(
        verbose_name="Is this the latest release?",
        default=False,
        db_index=True,
        help_text="Set this if this should be considered the latest release "
        "for the major version. Previous 'latest' versions will "
        "automatically have this flag turned off.",
    )
    is_published = models.BooleanField(
        verbose_name="Is Published?",
        default=False,
        db_index=True,
        help_text="Whether or not this should be considered a released/published version",
    )
    pre_release = models.BooleanField(
        verbose_name="Pre-release",
        default=False,
        db_index=True,
        help_text="Boolean to denote pre-release/beta/RC versions",
    )
    show_on_download_page = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether or not to show this release on the main /downloads/ page",
    )
    release_date = models.DateTimeField(default=timezone.now)
    release_page = models.ForeignKey(
        Page,
        related_name="release",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    release_notes_url = models.URLField("Release Notes URL", blank=True)

    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE, default="")

    objects = ReleaseManager()

    class Meta:
        """Meta configuration for Release."""

        verbose_name = "Release"
        verbose_name_plural = "Releases"
        ordering = ("name",)
        get_latest_by = "release_date"

    def __str__(self):
        """Return string representation."""
        return self.name

    def get_absolute_url(self):
        """Return the URL for this release's detail page or its release page."""
        if not self.content.raw and self.release_page:
            return self.release_page.get_absolute_url()
        return reverse("download:download_release_detail", kwargs={"release_slug": self.slug})

    def download_file_for_os(self, os_slug):
        """Given an OS slug return the appropriate download file."""
        try:
            file = self.files.get(os__slug=os_slug, download_button=True)
        except ReleaseFile.DoesNotExist:
            file = None

        return file

    def files_for_os(self, os_slug):
        """Return all files for this release for a given OS."""
        return self.files.filter(os__slug=os_slug).order_by("-name")

    def get_version(self):
        """Extract the version number string from the release name."""
        version = re.match(r"Python\s([\d.]+)", self.name)
        if version is not None:
            return version.group(1)
        return ""

    def is_version_at_least(self, min_version_tuple):
        """Check whether this release's version meets the minimum version tuple."""
        v1 = []
        for b in self.get_version().split("."):
            try:
                v1.append(int(b))
            except ValueError:
                break
        # If v1 (us) is shorter than v2 (the comparand), it will always fail.
        # Add zeros for the comparison.
        while len(min_version_tuple) > len(v1):
            v1.append(0)
        return tuple(v1) >= min_version_tuple

    @property
    def is_version_at_least_3_5(self):
        """Return True if this release is Python 3.5 or later."""
        return self.is_version_at_least((3, 5))

    @property
    def is_version_at_least_3_9(self):
        """Return True if this release is Python 3.9 or later."""
        return self.is_version_at_least((3, 9))

    @property
    def is_version_at_least_3_14(self):
        """Return True if this release is Python 3.14 or later."""
        return self.is_version_at_least((3, 14))


def update_supernav():
    """Regenerate the supernav download box with the latest release links."""
    latest_python3 = Release.objects.latest_python3()
    if not latest_python3:
        return

    try:
        latest_pymanager = Release.objects.latest_pymanager()
    except Release.DoesNotExist:
        latest_pymanager = None

    python_files = []
    for o in OS.objects.all():
        data = {
            "os": o,
            "python3": None,
            "pymanager": None,
        }

        data["python3"] = latest_python3.download_file_for_os(o.slug)
        if latest_pymanager:
            data["pymanager"] = latest_pymanager.download_file_for_os(o.slug)

        # Only include OSes that have at least one download file
        if data["python3"] or data["pymanager"]:
            python_files.append(data)

    if not python_files:
        return

    content = render_to_string(
        "downloads/supernav.html",
        {
            "python_files": python_files,
            "last_updated": timezone.now(),
        },
    )

    box, created = Box.objects.update_or_create(
        label="supernav-python-downloads",
        defaults={
            "content": content,
            "content_markup_type": "html",
        },
    )
    if not created:
        box.save()


def update_download_landing_sources_box():
    """Regenerate the download sources box with latest Python 2 and 3 source links."""
    latest_python2 = Release.objects.latest_python2()
    latest_python3 = Release.objects.latest_python3()

    context = {}

    if latest_python2:
        latest_python2_source = latest_python2.download_file_for_os("source")
        if latest_python2_source:
            context["latest_python2_source"] = latest_python2_source

    if latest_python3:
        latest_python3_source = latest_python3.download_file_for_os("source")
        if latest_python3_source:
            context["latest_python3_source"] = latest_python3_source

    if "latest_python2_source" not in context or "latest_python3_source" not in context:
        return

    source_content = render_to_string("downloads/download-sources-box.html", context)
    source_box, created = Box.objects.update_or_create(
        label="download-sources",
        defaults={
            "content": source_content,
            "content_markup_type": "html",
        },
    )
    if not created:
        source_box.save()


def update_homepage_download_box():
    """Regenerate the homepage download box with latest Python versions."""
    latest_python2 = Release.objects.latest_python2()
    latest_python3 = Release.objects.latest_python3()

    context = {}

    if latest_python2:
        context["latest_python2"] = latest_python2

    if latest_python3:
        context["latest_python3"] = latest_python3

    if "latest_python2" not in context or "latest_python3" not in context:
        return

    content = render_to_string("downloads/homepage-downloads-box.html", context)

    box, created = Box.objects.update_or_create(
        label="homepage-downloads",
        defaults={
            "content": content,
            "content_markup_type": "html",
        },
    )
    if not created:
        box.save()


@receiver(post_save, sender=Release)
def promote_latest_release(sender, instance, **kwargs):
    """Promote this release to be the latest if this flag is set."""
    # Skip in fixtures
    if kwargs.get("raw", False):
        return

    if instance.is_latest:
        # Demote all previous instances
        Release.objects.filter(version=instance.version).exclude(pk=instance.pk).update(is_latest=False)


@receiver(post_save, sender=Release)
def purge_fastly_download_pages(sender, instance, **kwargs):
    """Purge Fastly caches so new Downloads show up more quickly.

    Uses surrogate key purging to attempt to clear ALL pages under /downloads/
    in one request, including dynamically added pages like /downloads/android/,
    /downloads/ios/, etc. Independently purges a set of specific non-/downloads/
    URLs via individual URL purges.
    """
    # Don't purge on fixture loads
    if kwargs.get("raw", False):
        return

    # Only purge on published instances
    if instance.is_published:
        # Purge all /downloads/* pages via surrogate key (preferred method)
        # This catches everything: /downloads/android/, /downloads/release/*, etc.
        # Falls back to purge_url if FASTLY_SERVICE_ID is not configured.
        if getattr(settings, "FASTLY_SERVICE_ID", None):
            purge_surrogate_key("downloads")
        else:
            purge_url("/downloads/")

        # Also purge related pages outside /downloads/
        purge_url("/ftp/python/")
        if instance.get_version():
            purge_url(f"/ftp/python/{instance.get_version()}/")
        # See issue #584 for details - these are under /box/, not /downloads/
        purge_url("/box/supernav-python-downloads/")
        purge_url("/box/homepage-downloads/")
        purge_url("/box/download-sources/")


@receiver(post_save, sender=Release)
def update_download_supernav_and_boxes(sender, instance, **kwargs):
    """Refresh supernav and download boxes when a release is saved."""
    # Skip in fixtures
    if kwargs.get("raw", False):
        return

    if instance.is_published:
        update_supernav()
        update_download_landing_sources_box()
        update_homepage_download_box()


def _update_boxes_for_release_file(instance):
    """Update supernav and download boxes if the file's release is published."""
    if instance.release_id and instance.release.is_published:
        update_supernav()
        update_download_landing_sources_box()
        update_homepage_download_box()
        purge_url("/box/supernav-python-downloads/")
        purge_url("/box/homepage-downloads/")
        purge_url("/box/download-sources/")


@receiver(post_save, sender="downloads.ReleaseFile")
def update_boxes_on_release_file_save(sender, instance, **kwargs):
    """Refresh supernav when a release file is added or changed."""
    if kwargs.get("raw", False):
        return
    _update_boxes_for_release_file(instance)


@receiver(post_delete, sender="downloads.ReleaseFile")
def update_boxes_on_release_file_delete(sender, instance, **kwargs):
    """Refresh supernav when a release file is deleted."""
    _update_boxes_for_release_file(instance)


def condition_url_is_blank_or_python_dot_org(column: str):
    """Conditions for a URLField column to force 'http[s]://python.org'."""
    return (
        models.Q(**{f"{column}__exact": ""})
        | models.Q(**{f"{column}__startswith": "https://www.python.org/"})
        # Older releases allowed 'http://'. 'https://' is required at
        # the API level, so shouldn't show up in newer releases.
        | models.Q(**{f"{column}__startswith": "http://www.python.org/"})
    )


class ReleaseFile(ContentManageable, NameSlugModel):
    """Individual files in a release.

    If a specific OS/release combo has multiple versions for example
    Windows and MacOS 32 vs 64 bit each file needs to be added separately.
    """

    os = models.ForeignKey(
        OS,
        related_name="releases",
        verbose_name="OS",
        on_delete=models.CASCADE,
    )
    release = models.ForeignKey(Release, related_name="files", on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    is_source = models.BooleanField("Is Source Distribution", default=False)
    url = models.URLField("URL", unique=True, db_index=True, help_text="Download URL")
    gpg_signature_file = models.URLField("GPG SIG URL", blank=True, help_text="GPG Signature URL")
    sigstore_signature_file = models.URLField("Sigstore Signature URL", blank=True, help_text="Sigstore Signature URL")
    sigstore_cert_file = models.URLField("Sigstore Cert URL", blank=True, help_text="Sigstore Cert URL")
    sigstore_bundle_file = models.URLField("Sigstore Bundle URL", blank=True, help_text="Sigstore Bundle URL")
    sbom_spdx2_file = models.URLField("SPDX-2 SBOM URL", blank=True, help_text="SPDX-2 SBOM URL")
    md5_sum = models.CharField("MD5 Sum", max_length=200, blank=True)
    sha256_sum = models.CharField("SHA256 Sum", max_length=200, blank=True)
    filesize = models.IntegerField(default=0)
    download_button = models.BooleanField(default=False, help_text="Use for the supernav download button for this OS")

    def validate_unique(self, exclude=None):
        """Ensure only one release file per OS has the download button enabled."""
        if self.download_button and self.release_id:
            qs = ReleaseFile.objects.filter(release=self.release, os=self.os, download_button=True).exclude(pk=self.id)
            if qs.count() > 0:
                msg = 'Only one Release File per OS can have "Download button" enabled'
                raise ValidationError(msg)
        super().validate_unique(exclude=exclude)

    class Meta:
        """Meta configuration for ReleaseFile."""

        verbose_name = "Release File"
        verbose_name_plural = "Release Files"
        ordering = ("-release__is_published", "release__name", "os__name", "name")

        constraints = [
            models.UniqueConstraint(
                fields=["os", "release"],
                condition=models.Q(download_button=True),
                name="only_one_download_per_os_per_release",
            ),
            models.CheckConstraint(
                condition=(
                    condition_url_is_blank_or_python_dot_org("url")
                    & condition_url_is_blank_or_python_dot_org("gpg_signature_file")
                    & condition_url_is_blank_or_python_dot_org("sigstore_signature_file")
                    & condition_url_is_blank_or_python_dot_org("sigstore_cert_file")
                    & condition_url_is_blank_or_python_dot_org("sigstore_bundle_file")
                    & condition_url_is_blank_or_python_dot_org("sbom_spdx2_file")
                ),
                name="only_python_dot_org_urls",
                violation_error_message="All file URLs must begin with 'https://www.python.org/'",
            ),
        ]
