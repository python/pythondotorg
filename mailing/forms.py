"""Forms for the mailing app."""

from django import forms
from django.template import Context, Template, TemplateSyntaxError

from mailing.models import BaseEmailTemplate


class BaseEmailTemplateForm(forms.ModelForm):
    """Form for editing email templates with Django template syntax validation."""

    def clean_content(self):
        """Validate that the content field contains valid Django template syntax."""
        content = self.cleaned_data["content"]
        try:
            template = Template(content)
            template.render(Context({}))
        except TemplateSyntaxError as e:
            raise forms.ValidationError(e) from e
        else:
            return content

    class Meta:
        """Meta configuration for BaseEmailTemplateForm."""

        model = BaseEmailTemplate
        fields = ["internal_name", "subject", "content"]
