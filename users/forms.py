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

    class Meta(object):
        model = User
        fields = [
            'bio',
            'search_visibility',
            'email_privacy',
        ]
        widgets = {
            'search_visibility': forms.RadioSelect,
            'email_privacy': forms.RadioSelect,
        }


class MembershipForm(ModelForm):

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

        self.fields['legal_name'].required = True
        self.fields['preferred_name'].required = True
        self.fields['city'].required = True
        self.fields['region'].required = True
        self.fields['country'].required = True
        self.fields['postal_code'].required = True

        code_of_conduct = self.fields['psf_code_of_conduct']
        code_of_conduct.widget = forms.RadioSelect(choices=self.COC_CHOICES)
        code_of_conduct.initial = True

        announcements = self.fields['psf_announcements']
        announcements.widget = forms.RadioSelect(choices=self.ACCOUNCEMENT_CHOICES)
        announcements.initial = True

    class Meta(object):
        model = User
        fields = [
            'legal_name',
            'preferred_name',
            'city',
            'region',
            'country',
            'postal_code',
            'psf_code_of_conduct',
            'psf_announcements',
        ]

    def clean(self):
        cleaned_data = super().clean()
        code_of_conduct = cleaned_data.get('psf_code_of_conduct')
        if code_of_conduct is not True:
            msg = 'Agreeing to the code of conduct is required.'
            self._errors['psf_code_of_conduct'] = msg
            del cleaned_data['psf_code_of_conduct']
        return cleaned_data
