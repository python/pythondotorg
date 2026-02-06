from celery import shared_task
from django.core.management import call_command


@shared_task
def close_expired_fellow_nominations():
    """Close Fellow nominations that have passed their expiry round."""
    call_command("close_expired_fellow_nominations")
