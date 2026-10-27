"""Celery application configuration for python.org background tasks."""

import os

from celery import Celery
from celery.signals import setup_logging
from django.core import management
from django_structlog.celery.steps import DjangoStructLogInitStep

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pydotorg.settings.local")

app = Celery("pydotorg")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.steps["worker"].add(DjangoStructLogInitStep)


@setup_logging.connect
def configure_logging(**kwargs):
    """Use Django's LOGGING for worker and beat instead of Celery's own handlers."""
    from django.conf import settings
    from django.utils.log import configure_logging as configure_django_logging

    configure_django_logging(settings.LOGGING_CONFIG, settings.LOGGING)


@app.task(bind=True)
def run_management_command(self, command_name, args, kwargs):
    """Execute a Django management command as an async Celery task."""
    management.call_command(command_name, *args, **kwargs)


app.autodiscover_tasks()
