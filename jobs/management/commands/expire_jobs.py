import datetime

from django.core.management import BaseCommand
from django.conf import settings
from django.utils import timezone

from jobs.models import Job


class Command(BaseCommand):
    """ Expire jobs older than settings.JOB_THRESHOLD_DAYS """

    def handle(self, **options):
        days = getattr(settings, 'JOB_THRESHOLD_DAYS', 90)
        expiration = timezone.now() - datetime.timedelta(days=days)

        Job.objects.approved().filter(
            expires__lte=expiration
        ).update(
            status=Job.STATUS_EXPIRED
        )
