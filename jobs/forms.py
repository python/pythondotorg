"""Forms for creating, editing, and reviewing job listings."""

from django import forms
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput
from markupfield.widgets import MarkupTextarea

from cms.forms import ContentManageableModelForm
from jobs.models import Job, JobReviewComment


class JobForm(ContentManageableModelForm):
    """Form for creating and editing job listings."""

    required_css_class = "required"

    class Meta:
        """Meta configuration for JobForm."""

        model = Job
        fields = (
            "job_title",
            "company_name",
            "category",
            "job_types",
            "other_job_type",
            "city",
            "region",
            "country",
            "description",
            "requirements",
            "company_description",
            "contact",
            "email",
            "url",
            "telecommuting",
            "agencies",
        )
        widgets = {
            "job_types": CheckboxSelectMultiple(),
        }
        help_texts = {
            "email": (
                "<b>This email address will be publicly displayed for "
                "applicants to contact if they are interested in the "
                "posting.</b>"
            ),
        }

    def __init__(self, *args, **kwargs):
        """Remove the default help text from the job_types field."""
        super().__init__(*args, **kwargs)
        self.fields["job_types"].help_text = None

    def save(self, commit=True):
        """Save the job and re-assign job types from cleaned data."""
        obj = super().save()
        obj.job_types.clear()
        for t in self.cleaned_data["job_types"]:
            obj.job_types.add(t)
        return obj


class JobReviewCommentForm(ContentManageableModelForm):
    """Form for adding review comments to job listings."""

    # We set 'required' to False because we can also set Job's status.
    # See JobReviewCommentCreate.form_valid() for details.
    comment = forms.CharField(required=False, widget=MarkupTextarea())

    class Meta:
        """Meta configuration for JobReviewCommentForm."""

        model = JobReviewComment
        fields = ["job", "comment"]
        widgets = {
            "job": HiddenInput(),
        }

    def save(self, commit=True):
        """Save the comment only if the comment field is non-empty."""
        # Don't try to add a new comment if the 'comment' field is empty.
        if self.cleaned_data["comment"]:
            return super().save(commit=commit)
        return None
