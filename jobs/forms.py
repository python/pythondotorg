from django import forms

from cms.forms import ContentManageableModelForm

from .models import Job


class JobForm(ContentManageableModelForm):
    class Meta:
        model = Job
        fields = (
            'category',
            'job_types',
            'company',
            'city',
            'region',
            'country',
            'description'
        )
