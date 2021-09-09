from django import forms
from django.utils.safestring import mark_safe

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
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    self_nomination = forms.BooleanField(
        required=False,
        help_text="If you are nominating yourself, we will automatically associate the nomination with your python.org user.",
    )

    def clean_self_nomination(self):
        data = self.cleaned_data["self_nomination"]
        if data:
            if not self.request.user.first_name or not self.request.user.last_name:
                raise forms.ValidationError(
                    mark_safe(
                        'You must set your First and Last name in your <a href="/users/edit/">User Profile</a> to self nominate.'
                    )
                )

        return data
