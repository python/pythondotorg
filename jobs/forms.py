from django import forms

from cms.forms import ContentManageableModelForm

from .models import Job


class JobForm(ContentManageableModelForm):
    class Meta:
        model = Job
