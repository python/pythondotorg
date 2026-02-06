"""App configuration for the jobs app."""

from django.apps import AppConfig


class JobsAppConfig(AppConfig):
    """Django app configuration for the job board."""

    name = "jobs"
    verbose_name = "Jobs Application"

    def ready(self):
        """Perform app initialization on startup."""
