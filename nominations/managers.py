from django.db import models
from django.db.models import Q
from django.utils import timezone


class FellowNominationQuerySet(models.QuerySet):
    def active(self):
        """Exclude accepted/not_accepted, keep nominations whose expiry round
        is still in the future OR whose expiry_round has not been set yet."""
        return self.exclude(status__in=["accepted", "not_accepted"]).filter(
            Q(expiry_round__quarter_end__gte=timezone.now().date()) | Q(expiry_round__isnull=True)
        )

    def for_round(self, round_obj):
        """Filter by nomination_round."""
        return self.filter(nomination_round=round_obj)

    def pending(self):
        return self.filter(status="pending")

    def accepted(self):
        return self.filter(status="accepted")
