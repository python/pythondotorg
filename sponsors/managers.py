from django.db.models.query import QuerySet


class SponsorQuerySet(QuerySet):
    def draft(self):
        return self.filter(is_published=False)

    def published(self):
        return self.filter(is_published=True)

    def featured(self):
        return self.published().filter(featured=True)
