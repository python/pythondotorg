from django.forms.widgets import CheckboxSelectMultiple

from .models import Feedback
from cms.forms import ContentManageableModelForm


class FeedbackForm(ContentManageableModelForm):

    class Meta(object):
        model = Feedback
        fields = (
            'name',
            'email',
            'country',
            'feedback_categories',
            'issue_type',
            'comment'
        )
        widgets = {
            'feedback_categories': CheckboxSelectMultiple()
        }


class FeedbackMiniForm(ContentManageableModelForm):
    class Meta(object):
        model = Feedback
        fields = (
            'comment',
        )
