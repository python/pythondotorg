from django.core.management.base import BaseCommand
from django.conf import settings

from fastly.utils import purge_surrogate_key


class Command(BaseCommand):
    """ Do things after deployment is complete """

    def handle(self, *args, **kwargs):
        # If we have a STATIC_SURROGATE_KEY set, purge static files to ensure
        # that anything cached mid-deploy is ignored (like 404s).
        if settings.STATIC_SURROGATE_KEY:
            purge_surrogate_key(settings.STATIC_SURROGATE_KEY)
