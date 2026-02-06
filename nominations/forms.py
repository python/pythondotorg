"""Forms for creating and managing board election nominations."""

from django import forms
from django.utils.safestring import mark_safe
from markupfield.widgets import MarkupTextarea

from nominations.models import Nomination


class NominationForm(forms.ModelForm):
    """Base form for editing a board election nomination."""

    class Meta:
        """Meta configuration for NominationForm."""

        model = Nomination
        fields = (
            "name",
            "email",
            "previous_board_service",
            "employer",
            "other_affiliations",
            "nomination_statement",
        )
        widgets = {"nomination_statement": MarkupTextarea()}  # , "self_nomination": forms.CheckboxInput()}
        help_texts = {
            "name": "Name of the person you are nominating.",
            "email": "Email address for the person you are nominating.",
            "previous_board_service": "Has the person previously served on the PSF Board? If so what year(s)? Otherwise 'New board member'.",
            "employer": "Nominee's current employer.",
            "other_affiliations": "Any other relevant affiliations the Nominee has.",
            "nomination_statement": "Markdown syntax supported.",
        }


class NominationCreateForm(NominationForm):
    """Form for creating a new nomination with optional self-nomination."""

    def __init__(self, *args, **kwargs):
        """Initialize form and extract the request from kwargs."""
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    self_nomination = forms.BooleanField(
        required=False,
        help_text="If you are nominating yourself, we will automatically associate the nomination with your python.org user.",
    )

    def clean_self_nomination(self):
        """Validate that self-nominating users have a first and last name set."""
        data = self.cleaned_data["self_nomination"]
        if data and (not self.request.user.first_name or not self.request.user.last_name):
            raise forms.ValidationError(
                mark_safe(
                    'You must set your First and Last name in your <a href="/users/edit/">User Profile</a> to self nominate.'
                )
            )

        return data


class NominationAcceptForm(forms.ModelForm):
    """Form for a nominee to accept or decline a nomination."""

    class Meta:
        """Meta configuration for NominationAcceptForm."""

        model = Nomination
        fields = ("accepted",)
        help_texts = {
            "accepted": "If selected, this nomination will be considered accepted and displayed once nominations are public.",
        }
