"""App configuration for the jobs app."""

from django.apps import AppConfig


class JobsAppConfig(AppConfig):
    """Django app configuration for the job board."""

    name = "apps.jobs"
    label = "jobs"
    verbose_name = "Jobs Application"

    def ready(self):
        """Perform app initialization on startup."""
        import apps.jobs.listeners  # noqa: F401
