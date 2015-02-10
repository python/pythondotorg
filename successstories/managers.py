from django.db.models import Manager
from django.db.models import Sum
from django.db.models.query import QuerySet


class StoryQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)

    def featured(self):
        return self.published().filter(featured=True)


class StoryManager(Manager):
    def get_queryset(self):
        return StoryQuerySet(self.model, using=self._db)

    def draft(self):
        return self.get_queryset().draft()

    def published(self):
        return self.get_queryset().published()

    def featured(self):
        return self.get_queryset().featured()

    def featured_weight_total(self):
        amount = self.featured().aggregate(total=Sum('weight'))
        if amount:
            return amount['total']
        return 0

