from django import forms
from django.db.models import Q
from django.utils.text import slugify

from .models import Story
from cms.forms import ContentManageableModelForm


class StoryForm(ContentManageableModelForm):
    pull_quote = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))

    class Meta:
        model = Story
        fields = (
            'name',
            'company_name',
            'company_url',
            'category',
            'author',
            'author_email',
            'pull_quote',
            'content'
        )
        labels = {
            'name': 'Story name',
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        slug = slugify(name)
        story = Story.objects.filter(Q(name=name) | Q(slug=slug)).exclude(pk=self.instance.pk)
        if name is not None and story.exists():
            raise forms.ValidationError('Please use a unique name.')
        return name
