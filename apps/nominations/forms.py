"""Forms for creating and managing board election nominations."""

import re

from django import forms
from django.utils import timezone
from django.utils.safestring import mark_safe
from markupfield.widgets import MarkupTextarea

from apps.nominations.models import ElectionKind, Nomination

COC_LABEL = mark_safe(
    "I agree to adhere to the Python Software Foundation's "
    '<a href="/psf/conduct/">Code of Conduct</a>, as well as the specific '
    "guidelines of each platform on which I engage, across PSF and Python "
    "community platforms (including but not limited to my nomination statement, "
    "Discuss.python.org, and PSF and Python-affiliated spaces) for the duration "
    "of this election cycle."
)

COC_HELP_TEMPLATE = (
    "Candidates are expected and required to maintain a safe and respectful "
    "environment on PSF and Python community platforms throughout the {cycle} "
    "election cycle. Moderation actions resulting from Code of Conduct violations "
    "or platform-specific guidelines are applied consistently to all community "
    "members, including {cycle} candidates."
)

VOTER_CLARITY_LABEL = (
    "I believe my nomination and the positions I advocate as a candidate are "
    "aligned with the current mission and bylaws of the Python Software "
    "Foundation, a 501(c)(3) nonprofit organization incorporated in the United "
    "States."
)

VOTER_CLARITY_HELP = (
    "Candidates are not required to be in full agreement with the PSF's current "
    "mission to stand for the PSF Board election. It is within a nominee's rights "
    "to run on a platform that differs from or challenges the PSF's current "
    "direction. This statement exists to provide voters with clarity on each "
    "candidate's position, so that each voter can make an informed choice. "
    "Candidates who do not check this box are equally eligible to stand for the "
    "PSF Board election."
)

PACKAGING_COUNCIL_ELIGIBILITY_LABEL = (
    "I confirm that I am a PSF voting member, that I am not currently employed by "
    "the Python Software Foundation as a staff member, and that I am not currently "
    "serving on the Python Steering Council."
)

PACKAGING_COUNCIL_ELIGIBILITY_HELP = mark_safe(
    "Packaging Council nominees must be PSF voting members. PSF staff members and "
    "currently serving Python Steering Council members are not eligible to stand "
    "for election to the Packaging Council, as defined in "
    '<a href="https://peps.python.org/pep-0772/">PEP 772</a>. If you are not yet '
    "a PSF voting member and would like to run for the Packaging Council, you can "
    "become one by signing up as a PSF Supporting Member or self-certifying as a "
    "PSF Contributing Member."
)

COC_REQUIRED_ERROR = "You must agree to the Code of Conduct acknowledgment to submit a self-nomination."

#: Earliest selectable service year per nomination form variant.
PREVIOUS_SERVICE_FIRST_YEAR = {
    ElectionKind.NominationFormVariant.BOARD: 2001,
    ElectionKind.NominationFormVariant.PACKAGING_COUNCIL: 2025,
}

#: Canonical stored value for candidates with no previous service.
NEW_MEMBER_LABEL = {
    ElectionKind.NominationFormVariant.BOARD: "New board member",
    ElectionKind.NominationFormVariant.PACKAGING_COUNCIL: "New Packaging Council member",
}


class NominationForm(forms.ModelForm):
    """Base form for editing a board election nomination."""

    #: Acknowledgment fields rendered separately by nomination_form.html.
    acknowledgment_field_names = ()

    def __init__(self, *args, **kwargs):
        """Pull the election off kwargs and apply its form settings."""
        self.election = kwargs.pop("election", None)
        self.variant = (
            self.election.nomination_form_variant if self.election else ElectionKind.NominationFormVariant.BOARD
        )
        super().__init__(*args, **kwargs)
        # The free-text model field is replaced by the structured yes/no +
        # year-picker pair below; its column is nullable, so an election with
        # hide_previous_service simply writes NULL.
        del self.fields["previous_board_service"]
        if not (self.election is not None and self.election.hide_previous_service):
            self._add_previous_service_fields()

    def _add_previous_service_fields(self):
        """Add the strict yes/no + year-picker pair for previous service."""
        label = self.election.previous_service_label if self.election else "Previous Board Service"
        years = [str(y) for y in range(timezone.now().year, PREVIOUS_SERVICE_FIRST_YEAR[self.variant] - 1, -1)]
        self.fields["previous_service"] = forms.ChoiceField(
            label=label,
            choices=(("no", "No — has not served before"), ("yes", "Yes — has served previously")),
            widget=forms.RadioSelect,
        )
        self.fields["previous_service_years"] = forms.MultipleChoiceField(
            label="Year(s) served",
            choices=[(y, y) for y in years],
            widget=forms.CheckboxSelectMultiple,
            required=False,
        )
        order = []
        for name in self.fields:
            if name == "email":
                order += [name, "previous_service", "previous_service_years"]
            elif name not in ("previous_service", "previous_service_years"):
                order.append(name)
        self.order_fields(order)
        # Best-effort prefill from the stored free-text value when editing.
        stored = self.instance.previous_board_service or ""
        stored_years = [y for y in re.findall(r"\b(?:19|20)\d{2}\b", stored) if y in years]
        if stored_years:
            self.fields["previous_service"].initial = "yes"
            self.fields["previous_service_years"].initial = stored_years
        elif stored:
            self.fields["previous_service"].initial = "no"

    def clean(self):
        """Compose the structured previous-service answer into the model field."""
        cleaned_data = super().clean()
        answer = cleaned_data.get("previous_service")
        if answer == "yes" and not cleaned_data.get("previous_service_years"):
            self.add_error("previous_service_years", "Select the year(s) served.")
        elif answer:
            value = (
                ", ".join(sorted(cleaned_data["previous_service_years"]))
                if answer == "yes"
                else NEW_MEMBER_LABEL[self.variant]
            )
            # The model field isn't on the form, so set the instance directly.
            self.instance.previous_board_service = value
        return cleaned_data

    @property
    def acknowledgment_fields(self):
        """Return the bound acknowledgment fields for separate template rendering."""
        return [self[name] for name in self.acknowledgment_field_names]

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
            "employer": "Nominee's current employer.",
            "other_affiliations": "Any other relevant affiliations the Nominee has.",
            "nomination_statement": "Markdown syntax supported.",
        }


class BaseNominationCreateForm(NominationForm):
    """Shared plumbing for the public nomination create forms.

    Subclasses declare the acknowledgment fields (whose wording varies per
    election kind) and list them in ``acknowledgment_field_names`` so the
    template can render them generically.
    """

    #: Acknowledgments that are mandatory only when self-nominating.
    self_nomination_required_acknowledgments = ()

    self_nomination = forms.BooleanField(
        required=False,
        help_text="If you are nominating yourself, we will automatically associate the nomination with your python.org user account.",
    )

    def __init__(self, *args, **kwargs):
        """Pull the request off kwargs before ModelForm init."""
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

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

    def clean(self):
        """Require the mandatory acknowledgments only for self-nominations."""
        cleaned_data = super().clean()
        if cleaned_data.get("self_nomination"):
            for name in self.self_nomination_required_acknowledgments:
                if not cleaned_data.get(name):
                    self.add_error(name, self.fields[name].error_messages["required"])
        else:
            # First-person attestations only apply to self-nominations; drop
            # any values posted with a third-party nomination.
            for name in self.acknowledgment_field_names:
                cleaned_data[name] = False
        return cleaned_data


class BoardNominationCreateForm(BaseNominationCreateForm):
    """Public nomination form for PSF Board elections."""

    acknowledgment_field_names = ("coc_acknowledged", "mission_alignment")
    self_nomination_required_acknowledgments = ("coc_acknowledged",)

    coc_acknowledged = forms.BooleanField(
        required=False,
        label=COC_LABEL,
        help_text=COC_HELP_TEMPLATE.format(cycle="PSF Board"),
        error_messages={"required": COC_REQUIRED_ERROR},
    )
    mission_alignment = forms.BooleanField(
        required=False,
        label=VOTER_CLARITY_LABEL,
        help_text=VOTER_CLARITY_HELP,
    )

    class Meta(NominationForm.Meta):
        """Meta configuration for BoardNominationCreateForm."""

        fields = (*NominationForm.Meta.fields, "coc_acknowledged", "mission_alignment")


class PackagingCouncilNominationCreateForm(BaseNominationCreateForm):
    """Public nomination form for Packaging Council elections."""

    acknowledgment_field_names = ("coc_acknowledged", "eligibility_confirmed")
    self_nomination_required_acknowledgments = ("coc_acknowledged", "eligibility_confirmed")

    coc_acknowledged = forms.BooleanField(
        required=False,
        label=COC_LABEL,
        help_text=COC_HELP_TEMPLATE.format(cycle="Packaging Council"),
        error_messages={"required": COC_REQUIRED_ERROR},
    )
    eligibility_confirmed = forms.BooleanField(
        required=False,
        label=PACKAGING_COUNCIL_ELIGIBILITY_LABEL,
        help_text=PACKAGING_COUNCIL_ELIGIBILITY_HELP,
        error_messages={"required": "You must confirm your eligibility to submit a Packaging Council self-nomination."},
    )

    class Meta(NominationForm.Meta):
        """Meta configuration for PackagingCouncilNominationCreateForm."""

        fields = (*NominationForm.Meta.fields, "coc_acknowledged", "eligibility_confirmed")


class NominationAcceptForm(forms.ModelForm):
    """Form for a nominee to accept or decline a nomination."""

    class Meta:
        """Meta configuration for NominationAcceptForm."""

        model = Nomination
        fields = ("accepted",)
        help_texts = {
            "accepted": "If selected, this nomination will be considered accepted and displayed once nominations are public.",
        }
