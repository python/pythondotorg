from django.db.models import Manager
from django.db.models.query import QuerySet


class StoryQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)


class StoryManager(Manager):
    def get_query_set(self):
        return StoryQuerySet(self.model, using=self._db)

    def draft(self):
        return self.get_query_set().draft()

    def published(self):
        return self.get_query_set().published()
