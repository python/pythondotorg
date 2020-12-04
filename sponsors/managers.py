from django.db.models.query import QuerySet


class SponsorshipQuerySet(QuerySet):
    def in_progress(self):
        status = [self.model.APPLIED, self.model.APPROVED]
        return self.filter(status__in=status)


class SponsorContactQuerySet(QuerySet):
    def get_primary_contact(self, sponsor):
        contact = self.filter(sponsor=sponsor, primary=True).first()
        if not contact:
            raise self.model.DoesNotExist()
        return contact
