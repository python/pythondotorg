"""Core pydotorg application configuration."""

from django.apps import AppConfig


class PyDotOrgConfig(AppConfig):
    """AppConfig for the pydotorg core application."""

    name = "pydotorg"

    def ready(self):
        """Register signal handlers."""
        import pydotorg.signals  # noqa: F401
