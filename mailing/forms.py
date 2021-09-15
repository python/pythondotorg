from django import forms
from django.template import Template, Context, TemplateSyntaxError

from mailing.models import BaseEmailTemplate


class BaseEmailTemplateForm(forms.ModelForm):

    def clean_content(self):
        content = self.cleaned_data["content"]
        try:
            template = Template(content)
            template.render(Context({}))
            return content
        except TemplateSyntaxError as e:
            raise forms.ValidationError(e)

    class Meta:
        model = BaseEmailTemplate
        fields = "__all__"
