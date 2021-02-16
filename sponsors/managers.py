from django.db.models import Q, Subquery
from django.db.models.query import QuerySet


class SponsorshipQuerySet(QuerySet):
    def in_progress(self):
        status = [self.model.APPLIED, self.model.APPROVED]
        return self.filter(status__in=status)

    def visible_to(self, user):
        contacts = user.sponsorcontact_set.values_list('sponsor_id', flat=True)
        status = [self.model.APPLIED, self.model.APPROVED, self.model.FINALIZED]
        return self.filter(
            Q(submited_by=user) | Q(sponsor_id__in=Subquery(contacts)),
            status__in=status,
        ).select_related('sponsor')
