import os

from celery import Celery
from django.core import management

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pydotorg.settings.local")

app = Celery("pydotorg")
app.config_from_object("django.conf:settings", namespace="CELERY")

@app.task(bind=True)
def run_management_command(self, command_name, args, kwargs):
    management.call_command(command_name, *args, **kwargs)

app.autodiscover_tasks()
