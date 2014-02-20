from django.forms.widgets import CheckboxSelectMultiple

from .models import Feedback
from cms.forms import ContentManageableModelForm


class FeedbackForm(ContentManageableModelForm):

    class Meta(object):
        model = Feedback
        fields = (
            'comment',
            'is_beta_tester',
            'email',
            'name',
            'country',
            'feedback_categories',
        )
        widgets = {
            'feedback_categories': CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['feedback_categories'].help_text = None
        self.fields['feedback_categories'].label = "What features of python.org are you most interested in?"
        self.fields['is_beta_tester'].label = 'Yes, consider me a Beta Tester!'

    def clean(self):
        cleaned_data = super().clean()
        is_beta_tester = cleaned_data.get('is_beta_tester')
        email = cleaned_data.get('email')

        if is_beta_tester and (not email or not len(email.strip())):
            msg = 'An email address is required for beta testers.'
            self._errors['email'] = self.error_class([msg])
            del cleaned_data['email']

        return cleaned_data


class FeedbackMiniForm(ContentManageableModelForm):
    class Meta(object):
        model = Feedback
        fields = (
            'comment',
        )
