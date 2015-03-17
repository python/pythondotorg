from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import ugettext_lazy as _

from django_comments_xtd.conf import settings as comments_settings
from django_comments_xtd.forms import CommentForm
from django_comments_xtd.models import TmpXtdComment

from .models import Job
from cms.forms import ContentManageableModelForm


class JobForm(ContentManageableModelForm):
    required_css_class = 'required'

    class Meta:
        model = Job
        fields = (
            'job_title',
            'company_name',
            'category',
            'job_types',
            'other_job_type',
            'city',
            'region',
            'country',
            'description',
            'requirements',
            'company_description',
            'contact',
            'email',
            'url',
            'telecommuting',
            'agencies',
        )
        widgets = {
            'job_types': CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job_types'].help_text = None


class JobCommentForm(CommentForm):
    reply_to = forms.IntegerField(required=True, initial=0, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        comment = kwargs.pop("comment", None)
        if comment:
            initial = kwargs.pop("initial", {})
            initial.update({"reply_to": comment.pk})
            kwargs["initial"] = initial
        super(JobCommentForm, self).__init__(*args, **kwargs)
        self.fields['name'] = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': _('name')}))
        self.fields['email'] = forms.EmailField(
            label=_("Email"), help_text=_("Required for comment verification"),
            widget=forms.TextInput(attrs={'placeholder': _('email')})
        )
        self.fields['url'] = forms.URLField(
            required=False,
            widget=forms.TextInput(attrs={'placeholder': _('website')}))
        self.fields['comment'] = forms.CharField(
            widget=forms.Textarea(attrs={'placeholder': _('comment')}),
            max_length=comments_settings.COMMENT_MAX_LENGTH)

    def get_comment_model(self):
        return TmpXtdComment

    def get_comment_create_data(self):
        data = super(JobCommentForm, self).get_comment_create_data()
        data.update({'thread_id': 0, 'level': 0, 'order': 1,
                     'parent_id': self.cleaned_data['reply_to'],
                     'followup': True})
        if comments_settings.COMMENTS_XTD_CONFIRM_EMAIL:
            # comment must be verified before getting approved
            data['is_public'] = False
        return data
