from django.db.models.query import QuerySet


class PostQuerySet(QuerySet):

    def public(self):
        return self.filter(status__exact=self.model.STATUS_PUBLIC)

    def private(self):
        return self.filter(status__in=[
            self.model.STATUS_PRIVATE,
        ])
