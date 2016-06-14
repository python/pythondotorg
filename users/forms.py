from django import forms
from django.forms import ModelForm

from .models import User, Membership


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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if email is not None and user.exists():
            raise forms.ValidationError('Please use a unique email address.')
        return email


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
