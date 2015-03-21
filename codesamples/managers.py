from django.db.models.query import QuerySet


class CodeSampleQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)
