"""Forms to be used in mailing tests."""

from apps.mailing.forms import BaseEmailTemplateForm
from apps.mailing.tests.models import MockEmailTemplate


class TestBaseEmailTemplateForm(BaseEmailTemplateForm):
    """Base email template form for testing."""

    class Meta:
        """Metaclass for the form."""

        model = MockEmailTemplate
        fields = "__all__"
