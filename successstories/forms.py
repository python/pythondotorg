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
