import datetime

from django import forms
from django.utils.safestring import mark_safe

from markupfield.widgets import MarkupTextarea

from .models import (
    FellowNomination,
    FellowNominationRound,
    FellowNominationVote,
    Nomination,
)


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


class NominationAcceptForm(forms.ModelForm):
    class Meta:
        model = Nomination
        fields = (
            "accepted",
        )
        help_texts = {
            "accepted": "If selected, this nomination will be considered accepted and displayed once nominations are public.",
        }


class FellowNominationForm(forms.ModelForm):
    """Form for submitting a PSF Fellow nomination."""

    class Meta:
        model = FellowNomination
        fields = (
            "nominee_name",
            "nominee_email",
            "nomination_statement",
        )
        widgets = {
            "nomination_statement": MarkupTextarea(),
        }
        help_texts = {
            "nominee_name": "Full name of the person you are nominating.",
            "nominee_email": "Email address for the person you are nominating.",
            "nomination_statement": "Why should this person be recognized as a PSF Fellow? Markdown supported.",
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean_nominee_email(self):
        email = self.cleaned_data["nominee_email"]
        if self.request and self.request.user.is_authenticated:
            if email.lower() == self.request.user.email.lower():
                raise forms.ValidationError(
                    "You cannot nominate yourself for PSF Fellow membership."
                )
        return email


class FellowNominationRoundForm(forms.ModelForm):
    """Admin form for creating/editing Fellow nomination rounds.

    Auto-populates date fields from year + quarter when dates are not
    explicitly provided, following the WG Charter schedule:
        - Nominations cutoff: 20th of month 2
        - Review start: same as nominations cutoff
        - Review end: 20th of month 3
    """

    # Quarter start/end date ranges per quarter number
    QUARTER_DATES = {
        FellowNominationRound.Q1: {
            "quarter_start": (1, 1),
            "quarter_end": (3, 31),
            "nominations_cutoff": (2, 20),
            "review_end": (3, 20),
        },
        FellowNominationRound.Q2: {
            "quarter_start": (4, 1),
            "quarter_end": (6, 30),
            "nominations_cutoff": (5, 20),
            "review_end": (6, 20),
        },
        FellowNominationRound.Q3: {
            "quarter_start": (7, 1),
            "quarter_end": (9, 30),
            "nominations_cutoff": (8, 20),
            "review_end": (9, 20),
        },
        FellowNominationRound.Q4: {
            "quarter_start": (10, 1),
            "quarter_end": (12, 31),
            "nominations_cutoff": (11, 20),
            "review_end": (12, 20),
        },
    }

    class Meta:
        model = FellowNominationRound
        fields = (
            "year",
            "quarter",
            "quarter_start",
            "quarter_end",
            "nominations_cutoff",
            "review_start",
            "review_end",
            "is_open",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default year to current year on create (not edit)
        if not self.instance.pk and not self.initial.get("year"):
            self.fields["year"].initial = datetime.date.today().year
        # Date fields are optional — auto-populated from year+quarter in clean()
        for field_name in ("quarter_start", "quarter_end", "nominations_cutoff",
                           "review_start", "review_end"):
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get("year")
        quarter = cleaned_data.get("quarter")

        if year and quarter:
            dates = self.QUARTER_DATES.get(quarter)
            if dates:
                # Auto-populate dates from year + quarter when not provided
                if not cleaned_data.get("quarter_start"):
                    month, day = dates["quarter_start"]
                    cleaned_data["quarter_start"] = datetime.date(year, month, day)

                if not cleaned_data.get("quarter_end"):
                    month, day = dates["quarter_end"]
                    cleaned_data["quarter_end"] = datetime.date(year, month, day)

                if not cleaned_data.get("nominations_cutoff"):
                    month, day = dates["nominations_cutoff"]
                    cleaned_data["nominations_cutoff"] = datetime.date(
                        year, month, day
                    )

                if not cleaned_data.get("review_start"):
                    # review_start == nominations_cutoff per WG Charter
                    cleaned_data["review_start"] = cleaned_data.get(
                        "nominations_cutoff"
                    )

                if not cleaned_data.get("review_end"):
                    month, day = dates["review_end"]
                    cleaned_data["review_end"] = datetime.date(year, month, day)

        # Validate date ordering
        quarter_start = cleaned_data.get("quarter_start")
        quarter_end = cleaned_data.get("quarter_end")
        review_start = cleaned_data.get("review_start")
        nominations_cutoff = cleaned_data.get("nominations_cutoff")

        if quarter_start and quarter_end and quarter_end <= quarter_start:
            raise forms.ValidationError(
                "Quarter end date must be after quarter start date."
            )

        if review_start and nominations_cutoff and review_start != nominations_cutoff:
            raise forms.ValidationError(
                "Review start date must equal the nominations cutoff date."
            )

        return cleaned_data


class FellowNominationManageForm(forms.ModelForm):
    """Admin/WG form for managing a Fellow nomination (full edit)."""

    class Meta:
        model = FellowNomination
        fields = (
            "nominee_name",
            "nominee_email",
            "nomination_statement",
            "status",
            "nominee_user",
        )
        widgets = {
            "nomination_statement": MarkupTextarea(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nominee_user"].required = False


class FellowNominationStatusForm(forms.ModelForm):
    """Minimal form for updating only the status of a Fellow nomination."""

    class Meta:
        model = FellowNomination
        fields = ("status",)


class FellowNominationVoteForm(forms.ModelForm):
    """Form for WG members to cast a vote on a Fellow nomination."""

    class Meta:
        model = FellowNominationVote
        fields = ("vote", "comment")
        widgets = {
            "vote": forms.RadioSelect,
        }
