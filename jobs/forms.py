from django.forms.widgets import CheckboxSelectMultiple

from .models import Job
from cms.forms import ContentManageableModelForm


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
            'description',
            'requirements',
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
        self.fields['telecommuting'].label = 'Is telecommuting allowed?'
        self.fields['agencies'].label = 'Is job on behalf of an agency?'
