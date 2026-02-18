"""Managers and querysets for filtering Python releases."""

from django.db.models import Manager
from django.db.models.query import QuerySet


class ReleaseQuerySet(QuerySet):
    """Custom queryset providing release filtering methods."""

    def published(self):
        """Return published releases."""
        return self.filter(is_published=True)

    def draft(self):
        """Return draft (unpublished) releases."""
        return self.filter(is_published=False)

    def downloads(self):
        """For the main downloads landing page."""
        return (
            self.select_related("release_page")
            .filter(
                is_published=True,
                show_on_download_page=True,
                pre_release=False,
            )
            .order_by("-release_date")
        )

    def python2(self):
        """Return published Python 2 releases."""
        return self.filter(version=2, is_published=True)

    def python3(self):
        """Return published Python 3 releases."""
        return self.filter(version=3, is_published=True)

    def pymanager(self):
        """Return published Python install manager releases."""
        return self.filter(version=100, is_published=True)

    def latest_python2(self):
        """Return the latest Python 2 release queryset."""
        return self.python2().filter(is_latest=True)

    def latest_python3(self, minor_version: int | None = None):
        """Return the latest Python 3 release, optionally for a specific minor version."""
        if minor_version is None:
            return self.python3().filter(is_latest=True)
        pattern = rf"^Python 3\.{minor_version}\."
        return self.python3().filter(name__regex=pattern).order_by("-release_date")

    def latest_prerelease(self):
        """Return the latest Python 3 prerelease queryset."""
        return self.python3().filter(pre_release=True).order_by("-release_date")

    def latest_pymanager(self):
        """Return the latest Python install manager release queryset."""
        return self.pymanager().filter(is_latest=True)

    def pre_release(self):
        """Return pre-release versions."""
        return self.filter(pre_release=True)

    def released(self):
        """Return published, non-pre-release versions."""
        return self.filter(is_published=True, pre_release=False)


class ReleaseManager(Manager.from_queryset(ReleaseQuerySet)):
    """Manager providing convenience methods that return single release instances."""

    def latest_python2(self):
        """Return the single latest Python 2 release or None."""
        return self.get_queryset().latest_python2().first()

    def latest_python3(self, minor_version: int | None = None):
        """Return the single latest Python 3 release or None."""
        return self.get_queryset().latest_python3(minor_version).first()

    def latest_prerelease(self):
        """Return the single latest Python 3 prerelease or None."""
        return self.get_queryset().latest_prerelease().first()

    def latest_pymanager(self):
        """Return the single latest Python install manager release or None."""
        return self.get_queryset().latest_pymanager().first()
