from django.db.models import Manager
from django.db.models.query import QuerySet


class ReleaseQuerySet(QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def draft(self):
        return self.filter(is_published=False)

    def downloads(self):
        """ For the main downloads landing page """
        return self.select_related('release_page').filter(
            is_published=True,
            show_on_download_page=True,
            pre_release=False,
        ).order_by('-release_date')

    def python2(self):
        return self.filter(version=2, is_published=True)

    def python3(self):
        return self.filter(version=3, is_published=True)

    def pymanager(self):
        return self.filter(version=100, is_published=True)

    def latest_python2(self):
        return self.python2().filter(is_latest=True)

    def latest_python3(self, minor_version: int | None = None):
        if minor_version is None:
            return self.python3().filter(is_latest=True)
        pattern = rf"^Python 3\.{minor_version}\."
        return self.python3().filter(name__regex=pattern).order_by("-release_date")

    def latest_prerelease(self):
        return self.python3().filter(pre_release=True).order_by("-release_date")

    def latest_pymanager(self):
        return self.pymanager().filter(is_latest=True)

    def pre_release(self):
        return self.filter(pre_release=True)

    def released(self):
        return self.filter(is_published=True, pre_release=False)


class ReleaseManager(Manager.from_queryset(ReleaseQuerySet)):
    def latest_python2(self):
        return self.get_queryset().latest_python2().first()

    def latest_python3(self, minor_version: int | None = None):
        return self.get_queryset().latest_python3(minor_version).first()

    def latest_prerelease(self):
        return self.get_queryset().latest_prerelease().first()

    def latest_pymanager(self):
        return self.get_queryset().latest_pymanager().first()
