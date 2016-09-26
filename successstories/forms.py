from django import forms

from .models import Story
from cms.forms import ContentManageableModelForm


class StoryForm(ContentManageableModelForm):
    class Meta:
        model = Story
        fields = (
            'name',
            'company_name',
            'company_url',
            'category',
            'author',
            'pull_quote',
            'content'
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        story = Story.objects.filter(name=name).exclude(pk=self.instance.pk)
        if name is not None and story.exists():
            raise forms.ValidationError('Please use a unique name.')
        return name
