from django.db import models
from django.utils import timezone


class FellowNominationQuerySet(models.QuerySet):
    def active(self):
        """Exclude accepted/not_accepted, filter by expiry_round still in future."""
        return self.exclude(
            status__in=["accepted", "not_accepted"]
        ).filter(
            expiry_round__quarter_end__gte=timezone.now().date()
        )

    def for_round(self, round_obj):
        """Filter by nomination_round."""
        return self.filter(nomination_round=round_obj)

    def pending(self):
        return self.filter(status="pending")

    def accepted(self):
        return self.filter(status="accepted")
