"""Forms for the success stories app."""

from django import forms
from django.db.models import Q
from django.utils.text import slugify

from cms.forms import ContentManageableModelForm

from .models import Story


class StoryForm(ContentManageableModelForm):
    """Form for submitting a new Python success story."""

    pull_quote = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}))

    class Meta:
        """Meta configuration for StoryForm."""

        model = Story
        fields = ("name", "company_name", "company_url", "category", "author", "author_email", "pull_quote", "content")
        labels = {
            "name": "Story name",
        }
        help_texts = {
            "content": "Note: Submissions in <a href='https://www.markdownguide.org/basic-syntax/'>Markdown</a> "
            "are strongly preferred and can be processed faster.",
        }

    def clean_name(self):
        """Validate that the story name and derived slug are unique."""
        name = self.cleaned_data.get("name")
        slug = slugify(name)
        story = Story.objects.filter(Q(name=name) | Q(slug=slug)).exclude(pk=self.instance.pk)
        if name is not None and story.exists():
            msg = "Please use a unique name."
            raise forms.ValidationError(msg)
        return name
