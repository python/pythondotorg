import logging

from celery import shared_task
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task
def close_expired_fellow_nominations():
    """Close Fellow nominations that have passed their expiry round."""
    try:
        call_command("close_expired_fellow_nominations")
    except Exception:
        logger.exception("Failed to close expired Fellow nominations")
        raise
