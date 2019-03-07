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
        widgets = {"nomination_statement": MarkupTextarea()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save()
        return obj
