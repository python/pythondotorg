from django.db.models.query import QuerySet


class PageQuerySet(QuerySet):
    def published(self):
        return self.filter(is_published=True)

    def draft(self):
        return self.filter(is_published=False)
