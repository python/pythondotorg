"""Forms for creating and managing board election nominations."""

from django import forms
from django.utils.safestring import mark_safe
from markupfield.widgets import MarkupTextarea

from apps.nominations.models import Nomination

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

PACKAGING_COUNCIL_PREVIOUS_SERVICE_HELP = (
    "Has the person previously served on the Packaging Council? If so, what "
    "year(s)? Otherwise, please add 'New Packaging Council member'."
)

COC_REQUIRED_ERROR = "You must agree to the Code of Conduct acknowledgment to submit a self-nomination."


class PackagingCouncilPreviousServiceMixin:
    """Relabel the previous-service field for Packaging Council forms.

    Used by both the create and edit forms so the field is presented
    consistently. The label comes from ``Election.previous_service_label`` so
    forms and read-only pages stay in sync.
    """

    def __init__(self, *args, **kwargs):
        """Relabel the previous-service field for the Packaging Council."""
        super().__init__(*args, **kwargs)
        field = self.fields.get("previous_board_service")
        if field is not None and self.election is not None:
            field.label = self.election.previous_service_label
            field.help_text = PACKAGING_COUNCIL_PREVIOUS_SERVICE_HELP


class NominationForm(forms.ModelForm):
    """Base form for editing a board election nomination."""

    #: Acknowledgment fields rendered separately by nomination_form.html.
    acknowledgment_field_names = ()

    def __init__(self, *args, **kwargs):
        """Pull the election off kwargs and apply its form settings."""
        self.election = kwargs.pop("election", None)
        super().__init__(*args, **kwargs)
        # blank=False is a form-layer check only; the DB column is nullable, so
        # omitting the field writes NULL rather than failing to save.
        if self.election is not None and self.election.hide_previous_service:
            self.fields.pop("previous_board_service", None)

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
            "previous_board_service": "Has the person previously served on the PSF Board? If so what year(s)? Otherwise 'New board member'.",
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


class PackagingCouncilNominationCreateForm(PackagingCouncilPreviousServiceMixin, BaseNominationCreateForm):
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


class PackagingCouncilNominationEditForm(PackagingCouncilPreviousServiceMixin, NominationForm):
    """Edit form for an existing Packaging Council nomination."""


class NominationAcceptForm(forms.ModelForm):
    """Form for a nominee to accept or decline a nomination."""

    class Meta:
        """Meta configuration for NominationAcceptForm."""

        model = Nomination
        fields = ("accepted",)
        help_texts = {
            "accepted": "If selected, this nomination will be considered accepted and displayed once nominations are public.",
        }
