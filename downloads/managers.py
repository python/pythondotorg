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

    def latest_python2(self):
        return self.python2().filter(is_latest=True)

    def latest_python3(self):
        return self.python3().filter(is_latest=True)

    def pre_release(self):
        return self.filter(pre_release=True)

    def released(self):
        return self.filter(is_published=True, pre_release=False)


class ReleaseManager(Manager):
    def get_queryset(self):
        return ReleaseQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def draft(self):
        return self.get_queryset().draft()

    def downloads(self):
        """ For the main downloads landing page """
        return self.get_queryset().downloads()

    def python2(self):
        return self.get_queryset().python2()

    def python3(self):
        return self.get_queryset().python3()

    def latest_python2(self):
        qs = self.get_queryset().latest_python2()
        if qs:
            return qs[0]
        else:
            return None

    def latest_python3(self):
        qs = self.get_queryset().latest_python3()
        if qs:
            return qs[0]
        else:
            return None

    def pre_release(self):
        return self.get_queryset().pre_release()

    def released(self):
        return self.get_queryset().released()
