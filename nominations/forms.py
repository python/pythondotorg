from django import forms

from markupfield.widgets import MarkupTextarea

from .models import Nomination


class NominationForm(forms.ModelForm):

    class Meta:
        model = Nomination
        fields = (
            "name",
            "email",
            "previous_board_service",
            "employer",
            "other_affiliations",
            "nomination_statement",
        )
        widgets = {
            "nomination_statement": MarkupTextarea()
        }  # , "self_nomination": forms.CheckboxInput()}
        help_texts = {
            "name": "Name of the person you are nominating.",
            "email": "Email address for the person you are nominating.",
            "previous_board_service": "Has the person previously served on the PSF Board? If so what year(s)? Otherwise 'New board member'.",
            "employer": "Nominee's current employer.",
            "other_affiliations": "Any other relevant affiliations the Nominee has.",
            "nomination_statement": "Markdown syntax supported.",
        }


class NominationCreateForm(NominationForm):
    self_nomination = forms.BooleanField(
        required=False,
        help_text="If you are nominating yourself, we will automatically associate the nomination with your python.org user.",
    )
