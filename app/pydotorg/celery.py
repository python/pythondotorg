import os

from celery import Celery
from django.core import management

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.pydotorg.settings.local")

app = Celery("app.pydotorg")
app.config_from_object("django.conf:settings", namespace="CELERY")

@app.task(bind=True)
def run_management_command(self, command_name, args, kwargs):
    management.call_command(command_name, *args, **kwargs)

app.autodiscover_tasks()
