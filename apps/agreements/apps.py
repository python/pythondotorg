"""Django app configuration for PSF agreements."""

from django.apps import AppConfig


class AgreementsConfig(AppConfig):
    """Drafts, signatures, and published terms for every agreement the PSF signs."""

    name = "apps.agreements"
    label = "agreements"
    verbose_name = "Agreements"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        """Register the built-in document kinds."""
        from apps.agreements import kinds  # noqa: F401 - registers on import
        from apps.agreements.orders import kinds as order_kinds  # noqa: F401 - registers on import
