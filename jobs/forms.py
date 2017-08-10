from django import forms
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput

from markupfield.widgets import MarkupTextarea

from .models import Job, JobReviewComment
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

    def clean_city(self):
        city = self.cleaned_data['city'].strip()
        return city

    def clean_region(self):
        region = self.cleaned_data['region'].strip()
        return region

    def clean_country(self):
        country = self.cleaned_data['country'].strip()
        return country

    def save(self, commit=True):
        obj = super().save()
        obj.job_types.clear()
        for t in self.cleaned_data['job_types']:
            obj.job_types.add(t)
        return obj


class JobReviewCommentForm(ContentManageableModelForm):
    # We set 'required' to False because we can also set Job's status.
    # See JobReviewCommentCreate.form_valid() for details.
    comment = forms.CharField(required=False, widget=MarkupTextarea())

    class Meta:
        model = JobReviewComment
        fields = ['job', 'comment']
        widgets = {
            'job': HiddenInput(),
        }

    def save(self, commit=True):
        # Don't try to add a new comment if the 'comment' field is empty.
        if self.cleaned_data['comment']:
            return super().save(commit=commit)
