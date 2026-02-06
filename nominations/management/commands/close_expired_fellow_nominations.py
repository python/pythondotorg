from django.core.management.base import BaseCommand
from django.utils import timezone

from nominations.models import FellowNomination


class Command(BaseCommand):
    help = "Close Fellow nominations that have passed their expiry round."

    def handle(self, *args, **options):
        today = timezone.now().date()
        expired = FellowNomination.objects.filter(
            status__in=[FellowNomination.PENDING, FellowNomination.UNDER_REVIEW],
            expiry_round__quarter_end__lt=today,
        )
        count = 0
        for nomination in expired:
            nomination.status = FellowNomination.NOT_ACCEPTED
            nomination.save()
            count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Closed {count} expired Fellow nomination(s).")
        )
