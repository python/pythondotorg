from django.db.models.query import QuerySet


class MinutesQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)

    def latest(self):
        return self.published().order_by('-date')
