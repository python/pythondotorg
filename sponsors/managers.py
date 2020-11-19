from django.db.models.query import QuerySet


class SponsorshipQuerySet(QuerySet):
    def in_progress(self):
        status = [self.model.APPLIED, self.model.APPROVED]
        return self.filter(status__in=status)
