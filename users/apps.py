"""App configuration for the users app."""

from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    """App configuration for user accounts and profiles."""

    name = "users"
    verbose_name = "Users"

    def ready(self):
        """Perform app initialization when Django starts."""
        import users.listeners  # noqa: F401
