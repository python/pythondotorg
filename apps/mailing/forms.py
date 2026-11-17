"""Forms for the mailing app."""

from django import forms
from django.template import Context, TemplateSyntaxError

from apps.mailing.models import BaseEmailTemplate


def validate_template_syntax(value):
    """Raise ValidationError unless ``value`` is valid email template syntax."""
    try:
        template = BaseEmailTemplate.template_engine.from_string(value)
        template.render(Context({}))
    except TemplateSyntaxError as e:
        raise forms.ValidationError(e) from e


class BaseEmailTemplateForm(forms.ModelForm):
    """Form for editing email templates with Django template syntax validation."""

    def clean_subject(self):
        """Validate that the subject field contains valid Django template syntax."""
        subject = self.cleaned_data["subject"]
        validate_template_syntax(subject)
        return subject

    def clean_content(self):
        """Validate that the content field contains valid Django template syntax."""
        content = self.cleaned_data["content"]
        validate_template_syntax(content)
        return content

    class Meta:
        """Meta configuration for BaseEmailTemplateForm."""

        model = BaseEmailTemplate
        fields = ["internal_name", "subject", "content"]
