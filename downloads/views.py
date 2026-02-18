"""Views for the Python downloads section."""

import re
from datetime import datetime
from typing import Any

from django.contrib.syndication.views import Feed
from django.db.models import Case, IntegerField, Prefetch, When
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed
from django.views.generic import DetailView, ListView, RedirectView, TemplateView

from downloads.models import OS, Release, ReleaseFile


class DownloadLatestPython2(RedirectView):
    """Redirect to latest Python 2 release."""

    permanent = False

    def get_redirect_url(self, **kwargs):
        """Return the URL for the latest Python 2 release."""
        try:
            latest_python2 = Release.objects.latest_python2()
        except Release.DoesNotExist:
            latest_python2 = None

        if latest_python2:
            return latest_python2.get_absolute_url()
        return reverse("download")


class DownloadLatestPython3(RedirectView):
    """Redirect to latest Python 3 release, optionally for a specific minor."""

    permanent = False

    def get_redirect_url(self, **kwargs):
        """Return the URL for the latest Python 3 release."""
        minor_version = kwargs.get("minor")
        try:
            minor_version_int = int(minor_version) if minor_version else None
            latest_release = Release.objects.latest_python3(minor_version_int)
        except (ValueError, Release.DoesNotExist):
            latest_release = None

        if latest_release:
            return latest_release.get_absolute_url()
        return reverse("downloads:download")


class DownloadLatestPrerelease(RedirectView):
    """Redirect to latest Python 3 prerelease."""

    permanent = False

    def get_redirect_url(self, **kwargs):
        """Return the URL for the latest Python 3 prerelease."""
        try:
            latest_prerelease = Release.objects.latest_prerelease()
        except Release.DoesNotExist:
            latest_prerelease = None

        if latest_prerelease:
            return latest_prerelease.get_absolute_url()
        return reverse("downloads:download")


class DownloadLatestPyManager(RedirectView):
    """Redirect to latest Python install manager release."""

    permanent = False

    def get_redirect_url(self, **kwargs):
        """Return the URL for the latest Python install manager release."""
        try:
            latest_pymanager = Release.objects.latest_pymanager()
        except Release.DoesNotExist:
            latest_pymanager = None

        if latest_pymanager:
            return latest_pymanager.get_absolute_url()
        return reverse("downloads")


class DownloadBase:
    """Include latest releases in all views."""

    def get_context_data(self, **kwargs):
        """Add latest Python 2, 3, and pymanager releases to context."""
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "latest_python2": Release.objects.latest_python2(),
                "latest_python3": Release.objects.latest_python3(),
                "latest_pymanager": Release.objects.latest_pymanager(),
            }
        )
        return context


class DownloadHome(DownloadBase, TemplateView):
    """Main downloads landing page showing all available releases."""

    template_name = "downloads/index.html"

    def get_context_data(self, **kwargs):
        """Add release listings and per-OS download files to context."""
        context = super().get_context_data(**kwargs)
        try:
            latest_python2 = Release.objects.latest_python2()
        except Release.DoesNotExist:
            latest_python2 = None

        try:
            latest_python3 = Release.objects.latest_python3()
        except Release.DoesNotExist:
            latest_python3 = None

        latest_pymanager = context.get("latest_pymanager")

        python_files = []
        for o in OS.objects.all():
            data = {
                "os": o,
            }
            if latest_python2 is not None:
                data["python2"] = latest_python2.download_file_for_os(o.slug)
            if latest_python3 is not None:
                data["python3"] = latest_python3.download_file_for_os(o.slug)
            if latest_pymanager is not None:
                data["pymanager"] = latest_pymanager.download_file_for_os(o.slug)
            python_files.append(data)

        def version_key(release: Release) -> tuple[int, ...]:
            try:
                return tuple(int(x) for x in release.get_version().split("."))
            except ValueError:
                return (0,)

        releases = list(Release.objects.downloads())
        releases.sort(key=version_key, reverse=True)

        context.update(
            {
                "releases": releases,
                "latest_python2": latest_python2,
                "latest_python3": latest_python3,
                "python_files": python_files,
            }
        )

        return context


class DownloadFullOSList(DownloadBase, ListView):
    """List all available operating systems for downloads."""

    template_name = "downloads/full_os_list.html"
    context_object_name = "os_list"
    model = OS


class DownloadOSList(DownloadBase, DetailView):
    """List releases filtered by a specific operating system."""

    template_name = "downloads/os_list.html"
    context_object_name = "os"
    model = OS

    def get_context_data(self, **kwargs):
        """Add releases and pre-releases for the selected OS to context."""
        context = super().get_context_data(**kwargs)
        release_files = ReleaseFile.objects.select_related(
            "os",
        ).filter(os=self.object)
        context.update(
            {
                "os_slug": self.object.slug,
                "releases": Release.objects.released()
                .prefetch_related(
                    Prefetch("files", queryset=release_files),
                )
                .order_by("-release_date"),
                "pre_releases": Release.objects.published()
                .pre_release()
                .prefetch_related(
                    Prefetch("files", queryset=release_files),
                )
                .order_by("-release_date"),
            }
        )
        return context


class DownloadReleaseDetail(DownloadBase, DetailView):
    """Detail view for a specific Python release with its files."""

    template_name = "downloads/release_detail.html"
    model = Release
    context_object_name = "release"

    def get_object(self):
        """Retrieve the release by slug or raise 404."""
        try:
            return self.get_queryset().select_related().get(slug=self.kwargs["release_slug"])
        except self.model.DoesNotExist as e:
            raise Http404 from e

    def get_context_data(self, **kwargs):
        """Add release files, featured files, and superseded-by info to context."""
        context = super().get_context_data(**kwargs)

        # Add featured files (files with download_button=True)
        # Order: macOS first, Windows second, Source last
        context["featured_files"] = (
            self.object.files.filter(download_button=True)
            .annotate(
                os_order=Case(
                    When(os__slug="macos", then=1),
                    When(os__slug="windows", then=2),
                    When(os__slug="source", then=3),
                    default=4,
                    output_field=IntegerField(),
                )
            )
            .order_by("os_order")
        )

        # Manually add release files for better ordering
        context["release_files"] = []

        # Add source files
        context["release_files"].extend(list(self.object.files.filter(os__slug="source").order_by("name")))

        # Add all other OSes
        context["release_files"].extend(list(self.object.files.exclude(os__slug="source").order_by("os__slug", "name")))

        # Find the latest release in the feature series (such as 3.14.x)
        # to show a "superseded by" notice on older releases
        version = self.object.get_version()
        if version and self.object.version == Release.PYTHON3:
            match = re.match(r"^3\.(\d+)", version)
            if match:
                minor_version = int(match.group(1))
                latest_in_series = Release.objects.latest_python3(minor_version)
                if latest_in_series and latest_in_series.pk != self.object.pk:
                    context["latest_in_series"] = latest_in_series

        return context


class ReleaseFeed(Feed):
    """Generate an RSS feed of the latest Python releases.

    .. note:: It may seem like these are unused methods, but the superclass uses them
        using Django's Syndication framework.
        Docs: https://docs.djangoproject.com/en/4.2/ref/contrib/syndication/
    """

    feed_type = Rss201rev2Feed
    title = "Python Releases"
    description = "Latest Python releases from Python.org"

    @staticmethod
    def link() -> str:
        """Return the URL to the main downloads page."""
        return reverse("downloads:download")

    def items(self) -> list[dict[str, Any]]:
        """Return the latest Python releases."""
        return Release.objects.filter(is_published=True).order_by("-release_date")[:10]

    def item_title(self, item: Release) -> str:
        """Return the release name as the item title."""
        return item.name

    def item_description(self, item: Release) -> str:
        """Return the release date as the item description."""
        return f"Release date: {item.release_date}"

    def item_pubdate(self, item: Release) -> datetime | None:
        """Return the release date as the item publication date."""
        if item.release_date:
            if timezone.is_naive(item.release_date):
                return timezone.make_aware(item.release_date)
            return item.release_date
        return None


class ReleaseEditButton(TemplateView):
    """Render the release edit button (shown only to staff users).

    This endpoint is not cached, allowing the edit button to appear
    for staff users even when the release page itself is cached.
    """

    template_name = "downloads/release_edit_button.html"

    def get_context_data(self, **kwargs):
        """Add release primary key to context for the edit link."""
        context = super().get_context_data(**kwargs)
        context["release_pk"] = self.kwargs["pk"]
        return context
