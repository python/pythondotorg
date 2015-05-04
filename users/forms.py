from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.forms import ModelForm

from .models import User, Membership


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

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'bio',
            'search_visibility',
            'email_privacy',
            'public_profile',
        ]
        widgets = {
            'search_visibility': forms.RadioSelect,
            'email_privacy': forms.RadioSelect,
        }


class MembershipForm(ModelForm):
    """ PSF Membership creation form """

    COC_CHOICES = (
        ('', ''),
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
        code_of_conduct.widget = forms.Select(choices=self.COC_CHOICES)

        announcements = self.fields['psf_announcements']
        announcements.widget = forms.CheckboxInput()
        announcements.initial = False

    class Meta:
        model = Membership
        fields = [
            'legal_name',
            'preferred_name',
            'email_address',
            'city',
            'region',
            'country',
            'postal_code',
            'psf_code_of_conduct',
            'psf_announcements',
        ]

    def clean_psf_code_of_conduct(self):
        data = self.cleaned_data['psf_code_of_conduct']
        if not data:
            raise forms.ValidationError('Agreeing to the code of conduct is required.')
        return data


class MembershipUpdateForm(MembershipForm):
    """
    PSF Membership update form

    NOTE: This disallows changing of the members acceptance of the Code of
    Conduct on purpose per the PSF.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        del(self.fields['psf_code_of_conduct'])
        del(self.fields['psf_announcements'])
