from django.db.models import Manager
from django.db.models.query import QuerySet


class ReleaseQuerySet(QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def draft(self):
        return self.filter(is_published=False)

    def downloads(self):
        """ For the main downloads landing page """
        return self.filter(is_published=True, show_on_download_page=True)

    def python2(self):
        return self.filter(version=2)

    def python3(self):
        return self.filter(version=3)


class ReleaseManager(Manager):
    def get_query_set(self):
        return ReleaseQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_query_set().published()

    def draft(self):
        return self.get_query_set().draft()

    def downloads(self):
        """ For the main downloads landing page """
        return self.get_query_set().downloads()

    def python2(self):
        return self.get_query_set().python2()

    def python3(self):
        return self.get_query_set().python3()
