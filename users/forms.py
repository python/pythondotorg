from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.forms import ModelForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(self.error_messages['duplicate_username'])


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User


class UserProfileForm(ModelForm):

    COC_CHOICES = (
        (True, 'Yes'),
        (False, 'No')
    )
    ACCOUNCEMENT_CHOICES = (
        (True, 'Yes'),
        (False, 'No')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # probably should not be editable?
        code_of_conduct = self.fields['psf_code_of_conduct']
        code_of_conduct.widget = forms.RadioSelect(choices=self.COC_CHOICES)
        code_of_conduct.initial = True

        announcements = self.fields['psf_announcements']
        announcements.widget = forms.RadioSelect(choices=self.ACCOUNCEMENT_CHOICES)
        announcements.initial = True

    class Meta(object):
        model = User
        fields = [
            'bio',
            'city',
            'region',
            'country',
            'postal_code',
            'psf_code_of_conduct',
            'psf_announcements',
            'search_visibility',
            'email_privacy',
        ]
        widgets = {
            'search_visibility': forms.RadioSelect,
            'email_privacy': forms.RadioSelect,
        }
