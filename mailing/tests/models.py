"""Models to be used in mailing tests."""

from mailing.models import BaseEmailTemplate


class MockEmailTemplate(BaseEmailTemplate):
    """Mock model for BaseEmailTemplate to use in tests."""

    class Meta:
        """Metaclass for MockEmailTemplate to avoid creating a table in the database."""
        app_label = 'mailing'
        managed = False
