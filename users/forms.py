"""Forms for user profile editing and PSF membership management."""

from django import forms
from django.forms import ModelForm

from users.models import Membership, User


class UserProfileForm(ModelForm):
    """Form for editing user profile information."""

    class Meta:
        """Meta configuration for UserProfileForm."""

        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "bio",
            "search_visibility",
            "email_privacy",
            "public_profile",
        ]
        widgets = {
            "search_visibility": forms.RadioSelect,
            "email_privacy": forms.RadioSelect,
        }

    def clean_username(self):
        """Validate that the username is unique (case-insensitive)."""
        try:
            user = User.objects.get_by_natural_key(self.cleaned_data.get("username"))
        except User.MultipleObjectsReturned as e:
            msg = "A user with that username already exists."
            raise forms.ValidationError(msg) from e
        except User.DoesNotExist:
            return self.cleaned_data.get("username")
        if user == self.instance:
            return self.cleaned_data.get("username")
        msg = "A user with that username already exists."
        raise forms.ValidationError(msg)

    def clean_email(self):
        """Validate that the email address is unique across all users."""
        email = self.cleaned_data.get("email")
        user = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if email is not None and user.exists():
            msg = "Please use a unique email address."
            raise forms.ValidationError(msg)
        return email


class MembershipForm(ModelForm):
    """PSF Membership creation form."""

    COC_CHOICES = (("", ""), (True, "Yes"), (False, "No"))
    ACCOUNCEMENT_CHOICES = ((True, "Yes"), (False, "No"))

    def __init__(self, *args, **kwargs):
        """Initialize form with required fields and custom code of conduct widget."""
        super().__init__(*args, **kwargs)

        self.fields["legal_name"].required = True
        self.fields["preferred_name"].required = True
        self.fields["city"].required = True
        self.fields["region"].required = True
        self.fields["country"].required = True
        self.fields["postal_code"].required = True

        code_of_conduct = self.fields["psf_code_of_conduct"]
        code_of_conduct.widget = forms.Select(choices=self.COC_CHOICES)

    class Meta:
        """Meta configuration for MembershipForm."""

        model = Membership
        fields = [
            "legal_name",
            "preferred_name",
            "email_address",
            "city",
            "region",
            "country",
            "postal_code",
            "psf_code_of_conduct",
        ]

    def clean_psf_code_of_conduct(self):
        """Validate that the user has agreed to the PSF code of conduct."""
        data = self.cleaned_data["psf_code_of_conduct"]
        if not data:
            msg = "Agreeing to the code of conduct is required."
            raise forms.ValidationError(msg)
        return data


class MembershipUpdateForm(MembershipForm):
    """PSF Membership update form.

    NOTE: This disallows changing of the members acceptance of the Code of
    Conduct on purpose per the PSF.
    """

    def __init__(self, *args, **kwargs):
        """Initialize form and remove the code of conduct field."""
        super().__init__(*args, **kwargs)

        del self.fields["psf_code_of_conduct"]
