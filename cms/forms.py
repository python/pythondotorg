from django.conf import settings
from django.utils import timezone
from django import forms


class ContentManageableModelForm(forms.ModelForm):
    created = forms.DateTimeField(required=False)
    updated = forms.DateTimeField(required=False)
    creator = forms.ModelChoiceField(settings.AUTH_USER_MODEL, required=False, widget=forms.widgets.TextInput())

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_created(self):
        if self.instance is not None:
            return self.instance.created
        return timezone.now()

    def clean_updated(self):
        return timezone.now()

    def creator(self):
        if self.instance is not None:
            return self.instance.creator
        if self.request is not None and self.request.user.is_authenticated():
            return self.request.user
        return None
