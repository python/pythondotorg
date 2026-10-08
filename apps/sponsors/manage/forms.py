"""Forms for the sponsor management UI."""

import contextlib
import re

from django import forms
from django.core.validators import EmailValidator
from django.utils import timezone

from apps.sponsors.models import (
    SPONSOR_TEMPLATE_HELP_TEXT,
    EmailTargetableConfiguration,
    LegalClause,
    LogoPlacementConfiguration,
    ProvidedFileAssetConfiguration,
    ProvidedTextAssetConfiguration,
    RequiredImgAssetConfiguration,
    RequiredResponseAssetConfiguration,
    RequiredTextAssetConfiguration,
    Sponsor,
    SponsorContact,
    SponsorEmailNotificationTemplate,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
    TieredBenefitConfiguration,
)
from apps.sponsors.validators import validate_signed_contract

PSF_EMAIL_DOMAINS = ("python.org", "pyfound.org")

_psf_email_validator = EmailValidator()


def validate_psf_staff_email(value):
    """Require a python.org or pyfound.org email address."""
    value = (value or "").strip()
    if not value:
        message = "Enter an email address."
        raise forms.ValidationError(message)
    if re.search(r"[\r\n]", value) or "," in value or ";" in value:
        message = "Enter a single, valid email address."
        raise forms.ValidationError(message)
    _psf_email_validator(value)
    domain = value.rsplit("@", 1)[-1].casefold()
    if domain not in PSF_EMAIL_DOMAINS:
        message = "Email address must be an @python.org or @pyfound.org address."
        raise forms.ValidationError(message)
    return value


def _validate_optional_psf_email(value):
    value = (value or "").strip()
    if not value:
        return ""
    return validate_psf_staff_email(value)


def year_choices():
    """Return year choices for select widgets. Current year + 2 years forward, plus historical years with data."""
    current = timezone.now().year
    return [(y, str(y)) for y in range(current + 2, 2021, -1)]


class YearTaggedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """Checkbox list that tags each option with its object's year so the page can filter by year."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):  # noqa: PLR0913 - Django ChoiceWidget.create_option signature
        """Add a ``data-year`` attribute taken from the option's model instance."""
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-year"] = instance.year
        return option


class SponsorshipBenefitManageForm(forms.ModelForm):
    """Form for creating and editing sponsorship benefits.

    Packages and conflicting benefits from every year are rendered, tagged with
    their year, so the page can show only the selected year's options. ``clean``
    rejects choices that belong to a different year than the benefit.
    """

    class Meta:
        """Meta options."""

        model = SponsorshipBenefit
        fields = [
            "name",
            "description",
            "program",
            "packages",
            "package_only",
            "new",
            "unavailable",
            "standalone",
            "internal_description",
            "internal_value",
            "capacity",
            "soft_capacity",
            "year",
            "legal_clauses",
            "conflicts",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"style": "width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "style": "width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;resize:vertical;",
                }
            ),
            "internal_description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "style": "width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;resize:vertical;",
                }
            ),
            "packages": YearTaggedCheckboxSelectMultiple(),
            "conflicts": YearTaggedCheckboxSelectMultiple(),
            "legal_clauses": forms.CheckboxSelectMultiple(),
            "year": forms.Select(
                attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with year choices, a default year, and year-tagged related choices."""
        super().__init__(*args, **kwargs)
        self.fields["year"].widget = forms.Select(
            choices=[("", "---"), *year_choices()],
            attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"},
        )
        if not self.instance.pk and not self.initial.get("year"):
            with contextlib.suppress(SponsorshipCurrentYear.DoesNotExist):
                self.initial["year"] = SponsorshipCurrentYear.get_year()

        self.fields["packages"].queryset = SponsorshipPackage.objects.filter(year__isnull=False).order_by(
            "-year", "-sponsorship_amount"
        )
        conflicts = (
            SponsorshipBenefit.objects.filter(year__isnull=False)
            .select_related("program")
            .order_by("-year", "program__order", "order")
        )
        if self.instance.pk:
            conflicts = conflicts.exclude(pk=self.instance.pk)
        self.fields["conflicts"].queryset = conflicts
        self.fields["conflicts"].label_from_instance = lambda benefit: f"{benefit.program.name} > {benefit.name}"
        self.fields["legal_clauses"].queryset = LegalClause.objects.order_by("order")
        self.fields["legal_clauses"].label_from_instance = lambda clause: clause.internal_name

    def clean(self):
        """Reject packages and conflicts that belong to a different year than the benefit."""
        cleaned = super().clean()
        year = cleaned.get("year")
        if year:
            for field in ("packages", "conflicts"):
                other_year = [obj for obj in cleaned.get(field) or [] if obj.year != year]
                if other_year:
                    names = ", ".join(str(obj) for obj in other_year)
                    self.add_error(field, f"Not part of {year}: {names}. Untick them or change the year.")
        return cleaned


class SponsorshipPackageManageForm(forms.ModelForm):
    """Form for creating and editing sponsorship packages."""

    benefits = forms.ModelMultipleChoiceField(
        queryset=SponsorshipBenefit.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        """Meta options."""

        model = SponsorshipPackage
        fields = [
            "name",
            "slug",
            "sponsorship_amount",
            "advertise",
            "logo_dimension",
            "year",
            "allow_a_la_carte",
            "benefits",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"style": "width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
            "slug": forms.TextInput(
                attrs={"style": "width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
            "sponsorship_amount": forms.NumberInput(
                attrs={"style": "width:200px;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
            "logo_dimension": forms.NumberInput(
                attrs={"style": "width:120px;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with year choices and year-specific benefits."""
        super().__init__(*args, **kwargs)
        self.fields["year"].widget = forms.Select(
            choices=[("", "---"), *year_choices()],
            attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"},
        )
        filter_year = None
        if self.is_bound and self.data.get(self.add_prefix("year")):
            # Malformed years leave the benefit list empty; the year field reports the error
            with contextlib.suppress(TypeError, ValueError):
                filter_year = int(self.data.get(self.add_prefix("year")))
        elif self.instance and self.instance.year:
            filter_year = self.instance.year
        elif self.initial.get("year"):
            filter_year = self.initial["year"]
        else:
            with contextlib.suppress(SponsorshipCurrentYear.DoesNotExist):
                filter_year = SponsorshipCurrentYear.get_year()

        if filter_year:
            self.fields["benefits"].queryset = (
                SponsorshipBenefit.objects.filter(year=filter_year)
                .select_related("program")
                .order_by("program__order", "order", "name")
            )
        if self.instance and self.instance.pk:
            self.initial.setdefault("benefits", self.instance.benefits.values_list("pk", flat=True))

    def clean(self):
        """Reject a slug already used by another package in the same year."""
        cleaned = super().clean()
        slug = cleaned.get("slug")
        year = cleaned.get("year")
        if slug and year:
            duplicates = SponsorshipPackage.objects.filter(slug=slug, year=year).exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error("slug", f'Another {year} package already uses the slug "{slug}".')
        return cleaned

    def _save_m2m(self):
        """Persist reverse benefit associations after the package is saved."""
        super()._save_m2m()
        self.instance.benefits.set(self.cleaned_data["benefits"])


class CloneYearForm(forms.Form):
    """Form for cloning benefits and packages from one year to another."""

    source_year = forms.ChoiceField(
        label="Copy from year",
        widget=forms.Select(
            attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;min-width:120px;"}
        ),
    )
    target_year = forms.IntegerField(
        label="Copy to year",
        widget=forms.NumberInput(
            attrs={"style": "width:120px;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
        ),
    )
    clone_packages = forms.BooleanField(
        label="Clone packages (tiers)",
        required=False,
        initial=True,
    )
    clone_benefits = forms.BooleanField(
        label="Clone benefits",
        required=False,
        initial=True,
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with source year choices."""
        super().__init__(*args, **kwargs)
        # Populate source years from existing data
        benefit_years = SponsorshipBenefit.objects.values_list("year", flat=True).distinct().order_by("-year")
        self.fields["source_year"].choices = [(y, str(y)) for y in benefit_years if y]

    def clean_target_year(self):
        """Validate target year is in acceptable range."""
        year = self.cleaned_data["target_year"]
        current = timezone.now().year
        if year < current:
            msg = f"Target year must be {current} or later."
            raise forms.ValidationError(msg)
        return year

    def clean(self):
        """Validate source and target years are different."""
        cleaned = super().clean()
        source = cleaned.get("source_year")
        target = cleaned.get("target_year")
        if source and target and int(source) == target:
            msg = "Source and target years must be different."
            raise forms.ValidationError(msg)
        return cleaned


class BenefitFilterForm(forms.Form):
    """Form for filtering benefits in the list view."""

    year = forms.ChoiceField(required=False)
    program = forms.ModelChoiceField(
        queryset=SponsorshipProgram.objects.all(),
        required=False,
        empty_label="All programs",
    )
    package = forms.ModelChoiceField(
        queryset=SponsorshipPackage.objects.none(),
        required=False,
        empty_label="All packages",
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with year and package choices."""
        selected_year = kwargs.pop("selected_year", None)
        super().__init__(*args, **kwargs)
        benefit_years = SponsorshipBenefit.objects.values_list("year", flat=True).distinct().order_by("-year")
        self.fields["year"].choices = [("", "All years")] + [(y, str(y)) for y in benefit_years if y]
        packages = SponsorshipPackage.objects.order_by("-year", "-sponsorship_amount")
        self.fields["package"].queryset = packages.filter(year=selected_year) if selected_year else packages


class CurrentYearForm(forms.ModelForm):
    """Form for updating the active sponsorship year."""

    class Meta:
        """Meta options."""

        model = SponsorshipCurrentYear
        fields = ["year"]
        widgets = {
            "year": forms.NumberInput(
                attrs={"style": "width:120px;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
        }


INPUT_STYLE = (
    "width:100%;padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;box-sizing:border-box;"
)


class SponsorshipApproveForm(forms.ModelForm):
    """Form for approving a sponsorship — sets dates, fee, package."""

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
    )
    renewal = forms.BooleanField(
        required=False,
        help_text="Use renewal contract template instead of new sponsorship template.",
    )

    class Meta:
        """Meta options."""

        model = Sponsorship
        fields = ["start_date", "end_date", "package", "sponsorship_fee", "renewal"]
        widgets = {
            "package": forms.Select(attrs={"style": INPUT_STYLE}),
            "sponsorship_fee": forms.NumberInput(attrs={"style": INPUT_STYLE}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with year-filtered packages."""
        super().__init__(*args, **kwargs)
        # Filter packages to the sponsorship's year
        filter_year = self.instance.year if self.instance else None
        if filter_year:
            self.fields["package"].queryset = SponsorshipPackage.objects.filter(year=filter_year).order_by(
                "-sponsorship_amount"
            )

    def clean(self):
        """Validate that end date is after start date."""
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end <= start:
            msg = "End date must be after start date."
            raise forms.ValidationError(msg)
        return cleaned


class SponsorshipApproveSignedForm(SponsorshipApproveForm):
    """Form for approving a sponsorship with an already-signed contract."""

    signed_contract = forms.FileField(
        label="Signed contract document",
        help_text="Upload the final version of the signed contract (PDF or DOCX, at most 20 MB).",
        widget=forms.ClearableFileInput(attrs={"style": INPUT_STYLE, "accept": ".pdf,.docx"}),
        validators=[validate_signed_contract],
    )


class SponsorshipEditForm(forms.ModelForm):
    """Form for editing sponsorship details (package, fee, year)."""

    class Meta:
        """Meta options."""

        model = Sponsorship
        fields = ["package", "sponsorship_fee", "year"]
        widgets = {
            "package": forms.Select(attrs={"style": INPUT_STYLE}),
            "sponsorship_fee": forms.NumberInput(attrs={"style": INPUT_STYLE}),
            "year": forms.NumberInput(attrs={"style": "width:120px;" + INPUT_STYLE}),
        }
        help_texts = {
            "package": (
                "Changing the package does not change the benefits on this sponsorship; "
                "it will be marked as a custom package so you can review the benefits."
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with year-filtered packages."""
        super().__init__(*args, **kwargs)
        filter_year = self.instance.year
        if self.instance.pk and filter_year:
            self.fields["year"].disabled = True
        elif self.is_bound and self.data.get("year"):
            with contextlib.suppress(ValueError):
                filter_year = int(self.data["year"])
        if filter_year:
            self.fields["package"].queryset = SponsorshipPackage.objects.filter(year=filter_year).order_by(
                "-sponsorship_amount"
            )


class SponsorEditForm(forms.ModelForm):
    """Form for editing sponsor company info."""

    class Meta:
        """Meta options."""

        model = Sponsor
        fields = [
            "name",
            "description",
            "landing_page_url",
            "primary_phone",
            "mailing_address_line_1",
            "mailing_address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "description": forms.Textarea(attrs={"rows": 3, "style": INPUT_STYLE + "resize:vertical;"}),
            "landing_page_url": forms.URLInput(attrs={"style": INPUT_STYLE}),
            "primary_phone": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "mailing_address_line_1": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "mailing_address_line_2": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "city": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "state": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "postal_code": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "country": forms.Select(attrs={"style": INPUT_STYLE}),
        }


class SponsorshipFilterForm(forms.Form):
    """Filter form for the sponsorship list."""

    STATUS_CHOICES = [("", "All statuses"), *Sponsorship.STATUS_CHOICES]
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    year = forms.ChoiceField(required=False)
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search sponsor name...",
                "style": "padding:6px 10px;border:1px solid #ccc;border-radius:4px;font-size:13px;width:200px;",
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        """Initialize form with year choices from existing sponsorships."""
        super().__init__(*args, **kwargs)
        years = Sponsorship.objects.values_list("year", flat=True).distinct().order_by("-year")
        self.fields["year"].choices = [("", "All years")] + [(y, str(y)) for y in years if y]


class BenefitChoiceField(forms.ModelChoiceField):
    """ModelChoiceField that shows 'Program > Benefit Name' without year."""

    def label_from_instance(self, obj):
        """Return label as 'Program > Benefit Name'."""
        return f"{obj.program.name} > {obj.name}"


class AddBenefitToSponsorshipForm(forms.Form):
    """Form for adding a benefit to a sponsorship."""

    benefit = BenefitChoiceField(
        queryset=SponsorshipBenefit.objects.none(),
        widget=forms.Select(attrs={"style": INPUT_STYLE}),
        label="Benefit to add",
    )

    def __init__(self, *args, sponsorship=None, **kwargs):
        """Initialize form with benefits filtered by sponsorship year."""
        super().__init__(*args, **kwargs)
        if sponsorship and sponsorship.year:
            # Show benefits for this year that aren't already on the sponsorship
            existing_ids = sponsorship.benefits.values_list("sponsorship_benefit_id", flat=True)
            self.fields["benefit"].queryset = (
                SponsorshipBenefit.objects.filter(year=sponsorship.year)
                .exclude(pk__in=existing_ids)
                .select_related("program")
                .order_by("program__order", "order")
            )


class ExecuteContractForm(forms.Form):
    """Form for uploading a signed contract document."""

    signed_document = forms.FileField(
        label="Signed contract document",
        help_text="Upload the signed contract (PDF or DOCX, at most 20 MB).",
        widget=forms.ClearableFileInput(attrs={"style": INPUT_STYLE, "accept": ".pdf,.docx"}),
        validators=[validate_signed_contract],
    )


class InternalReviewEmailForm(forms.Form):
    """Shared internal-review recipient form: a single exact PSF-domain address."""

    internal_email = forms.CharField(
        label="Reviewer email",
        max_length=254,
        error_messages={"required": "Please enter an email address."},
    )

    def clean_internal_email(self):
        """Validate the reviewer email is a single exact PSF-domain address."""
        return validate_psf_staff_email(self.cleaned_data["internal_email"])


class ComposerRecipientsForm(forms.Form):
    """Optional extra recipients for a sponsor proposal send; each must be an exact PSF-domain address."""

    extra_to = forms.CharField(required=False, max_length=254)
    cc_email = forms.CharField(required=False, max_length=254)
    bcc_email = forms.CharField(required=False, max_length=254)

    def clean_extra_to(self):
        """Validate the optional extra "to" address."""
        return _validate_optional_psf_email(self.cleaned_data.get("extra_to"))

    def clean_cc_email(self):
        """Validate the optional CC address."""
        return _validate_optional_psf_email(self.cleaned_data.get("cc_email"))

    def clean_bcc_email(self):
        """Validate the optional BCC address."""
        return _validate_optional_psf_email(self.cleaned_data.get("bcc_email"))


class SendSponsorshipNotificationManageForm(forms.Form):
    """Form for sending email notifications to sponsorship contacts from the manage UI."""

    contact_types = forms.MultipleChoiceField(
        choices=SponsorContact.CONTACT_TYPES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Send to contact types",
    )
    notification = forms.ModelChoiceField(
        queryset=SponsorEmailNotificationTemplate.objects.all(),
        help_text="Select an existing notification template, or write custom content below.",
        required=False,
        label="Template",
    )
    subject = forms.CharField(
        max_length=140,
        required=False,
        widget=forms.TextInput(attrs={"style": INPUT_STYLE, "placeholder": "Custom email subject"}),
    )
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 8, "style": INPUT_STYLE + "resize:vertical;", "placeholder": "Custom email content"}
        ),
        required=False,
        help_text=SPONSOR_TEMPLATE_HELP_TEXT,
    )

    def clean(self):
        """Validate that either a notification template or custom content is provided, not both."""
        cleaned_data = super().clean()
        notification = cleaned_data.get("notification")
        subject = cleaned_data.get("subject", "").strip()
        content = cleaned_data.get("content", "").strip()
        custom_notification = subject or content

        if not (notification or custom_notification):
            msg = "You must select a template or provide custom subject and content."
            raise forms.ValidationError(msg)
        if notification and custom_notification:
            msg = "Select a template or use custom content, not both."
            raise forms.ValidationError(msg)

        return cleaned_data

    def get_notification(self):
        """Return the selected template or build one from custom fields."""
        default_notification = SponsorEmailNotificationTemplate(
            content=self.cleaned_data["content"],
            subject=self.cleaned_data["subject"],
        )
        return self.cleaned_data.get("notification") or default_notification


class NotificationTemplateForm(forms.ModelForm):
    """Form for creating and editing SponsorEmailNotificationTemplate instances."""

    class Meta:
        """Meta options."""

        model = SponsorEmailNotificationTemplate
        fields = ["internal_name", "subject", "content"]
        widgets = {
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "subject": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "content": forms.Textarea(attrs={"rows": 12, "style": INPUT_STYLE + "resize:vertical;"}),
        }
        help_texts = {
            "content": SPONSOR_TEMPLATE_HELP_TEXT,
        }


class SponsorContactForm(forms.ModelForm):
    """Form for adding/editing a sponsor contact."""

    class Meta:
        """Meta options."""

        model = SponsorContact
        fields = ["name", "email", "phone", "primary", "administrative", "accounting", "manager"]
        widgets = {
            "name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "email": forms.EmailInput(attrs={"style": INPUT_STYLE}),
            "phone": forms.TextInput(attrs={"style": INPUT_STYLE}),
        }


# ── Benefit Feature Configuration Forms ──


class BenefitConfigForm(forms.ModelForm):
    """Base form for a feature configuration, bound to the benefit it configures."""

    def __init__(self, *args, benefit, **kwargs):
        """Attach the benefit before validation so checks against its other configurations work."""
        super().__init__(*args, **kwargs)
        self.benefit = benefit
        self.instance.benefit = benefit

    def _other_configs(self, model_cls):
        """Return the benefit's other configurations of the given type."""
        return model_cls.objects.filter(benefit=self.benefit).exclude(pk=self.instance.pk)


_ASSET_CONFIG_MODELS = (
    RequiredImgAssetConfiguration,
    RequiredTextAssetConfiguration,
    RequiredResponseAssetConfiguration,
    ProvidedTextAssetConfiguration,
    ProvidedFileAssetConfiguration,
)


class AssetConfigForm(BenefitConfigForm):
    """Base form for asset configurations."""

    def clean(self):
        """Reject an internal name that another asset type already uses for the same owner.

        Sponsors and sponsorships hold one asset per internal name, so two asset
        types sharing a name would read and write the same stored value.
        Duplicates within one type are rejected by the model's unique constraint.
        """
        cleaned = super().clean()
        internal_name = cleaned.get("internal_name")
        related_to = cleaned.get("related_to")
        if internal_name and related_to:
            for model_cls in _ASSET_CONFIG_MODELS:
                if model_cls is self._meta.model:
                    continue
                clash = (
                    model_cls.objects.filter(internal_name=internal_name, related_to=related_to)
                    .select_related("benefit")
                    .first()
                )
                if clash:
                    self.add_error(
                        "internal_name",
                        f'"{internal_name}" is already used by a {clash._meta.verbose_name.lower()} on '  # noqa: SLF001 - Django _meta API access
                        f'"{clash.benefit.name}" ({clash.benefit.year}). Pick a different internal name.',
                    )
                    break
        return cleaned


class LogoPlacementConfigForm(BenefitConfigForm):
    """Form for LogoPlacementConfiguration."""

    class Meta:
        """Meta options."""

        model = LogoPlacementConfiguration
        fields = ["publisher", "logo_place", "link_to_sponsors_page", "describe_as_sponsor"]
        widgets = {
            "publisher": forms.Select(attrs={"style": INPUT_STYLE}),
            "logo_place": forms.Select(attrs={"style": INPUT_STYLE}),
        }


class TieredBenefitConfigForm(BenefitConfigForm):
    """Form for TieredBenefitConfiguration."""

    class Meta:
        """Meta options."""

        model = TieredBenefitConfiguration
        fields = ["package", "quantity", "display_label"]
        widgets = {
            "package": forms.Select(attrs={"style": INPUT_STYLE}),
            "quantity": forms.NumberInput(attrs={"style": INPUT_STYLE}),
            "display_label": forms.TextInput(attrs={"style": INPUT_STYLE}),
        }

    def __init__(self, *args, **kwargs):
        """Limit package choices to the benefit's year, keeping an already-saved package selectable."""
        super().__init__(*args, **kwargs)
        packages = SponsorshipPackage.objects.filter(year=self.benefit.year)
        if self.instance.package_id:
            packages |= SponsorshipPackage.objects.filter(pk=self.instance.package_id)
        self.fields["package"].queryset = packages.order_by("-sponsorship_amount")

    def clean_package(self):
        """Allow only one tier per package on a benefit."""
        package = self.cleaned_data["package"]
        if package and self._other_configs(TieredBenefitConfiguration).filter(package=package).exists():
            msg = f"{package} already has a tier on this benefit. Edit that configuration instead."
            raise forms.ValidationError(msg)
        return package


class EmailTargetableConfigForm(BenefitConfigForm):
    """Form for EmailTargetableConfiguration (no extra fields)."""

    class Meta:
        """Meta options."""

        model = EmailTargetableConfiguration
        fields = []

    def clean(self):
        """Allow a single email targetable configuration per benefit."""
        cleaned = super().clean()
        if self._other_configs(EmailTargetableConfiguration).exists():
            msg = "This benefit already has an Email Targetable configuration."
            raise forms.ValidationError(msg)
        return cleaned


class RequiredImgAssetConfigForm(AssetConfigForm):
    """Form for RequiredImgAssetConfiguration."""

    class Meta:
        """Meta options."""

        model = RequiredImgAssetConfiguration
        fields = [
            "related_to",
            "internal_name",
            "label",
            "help_text",
            "due_date",
            "min_width",
            "max_width",
            "min_height",
            "max_height",
        ]
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "due_date": forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
            "min_width": forms.NumberInput(attrs={"style": INPUT_STYLE}),
            "max_width": forms.NumberInput(attrs={"style": INPUT_STYLE}),
            "min_height": forms.NumberInput(attrs={"style": INPUT_STYLE}),
            "max_height": forms.NumberInput(attrs={"style": INPUT_STYLE}),
        }

    def clean(self):
        """Require each minimum dimension to be no larger than its maximum."""
        cleaned = super().clean()
        for low, high in (("min_width", "max_width"), ("min_height", "max_height")):
            low_value, high_value = cleaned.get(low), cleaned.get(high)
            if low_value is not None and high_value is not None and low_value > high_value:
                self.add_error(high, f"Must be at least the {self.fields[low].label.lower()} ({low_value}).")
        return cleaned


class RequiredTextAssetConfigForm(AssetConfigForm):
    """Form for RequiredTextAssetConfiguration."""

    max_length = forms.IntegerField(
        required=False,
        min_value=1,
        help_text="Limit to length of the input, empty means unlimited",
        widget=forms.NumberInput(attrs={"style": INPUT_STYLE}),
    )

    class Meta:
        """Meta options."""

        model = RequiredTextAssetConfiguration
        fields = ["related_to", "internal_name", "label", "help_text", "due_date", "max_length"]
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "due_date": forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
        }


class RequiredResponseAssetConfigForm(AssetConfigForm):
    """Form for RequiredResponseAssetConfiguration."""

    class Meta:
        """Meta options."""

        model = RequiredResponseAssetConfiguration
        fields = ["related_to", "internal_name", "label", "help_text", "due_date"]
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "due_date": forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
        }


class ProvidedTextAssetConfigForm(AssetConfigForm):
    """Form for ProvidedTextAssetConfiguration."""

    class Meta:
        """Meta options."""

        model = ProvidedTextAssetConfiguration
        fields = ["related_to", "internal_name", "label", "help_text", "shared", "shared_text"]
        labels = {"shared": "Shared with every sponsor", "shared_text": "Shared text"}
        help_texts = {"shared_text": "Shown to every sponsor when Shared is checked."}
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "shared_text": forms.Textarea(attrs={"rows": 5, "style": INPUT_STYLE + "resize:vertical;"}),
        }

    def clean(self):
        """Require the shared text when the asset is shared."""
        cleaned = super().clean()
        if cleaned.get("shared") and not cleaned.get("shared_text"):
            self.add_error("shared_text", "Enter the text to share, or uncheck Shared.")
        return cleaned


class ProvidedFileAssetConfigForm(AssetConfigForm):
    """Form for ProvidedFileAssetConfiguration."""

    class Meta:
        """Meta options."""

        model = ProvidedFileAssetConfiguration
        fields = ["related_to", "internal_name", "label", "help_text", "shared", "shared_file"]
        labels = {"shared": "Shared with every sponsor", "shared_file": "Shared file"}
        help_texts = {"shared_file": "Offered to every sponsor when Shared is checked."}
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
        }

    def clean(self):
        """Require the shared file when the asset is shared."""
        cleaned = super().clean()
        if cleaned.get("shared") and not cleaned.get("shared_file"):
            self.add_error("shared_file", "Upload the file to share, or uncheck Shared.")
        return cleaned


class ComposerSponsorForm(forms.ModelForm):
    """Form for creating a new sponsor inline within the composer wizard."""

    class Meta:
        """Meta options."""

        model = Sponsor
        fields = ["name", "description", "primary_phone", "city", "country"]
        widgets = {
            "name": forms.TextInput(attrs={"style": INPUT_STYLE, "placeholder": "Company name"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "style": INPUT_STYLE + "resize:vertical;", "placeholder": "Brief description"}
            ),
            "primary_phone": forms.TextInput(attrs={"style": INPUT_STYLE, "placeholder": "Phone number"}),
            "city": forms.TextInput(attrs={"style": INPUT_STYLE, "placeholder": "City"}),
            "country": forms.Select(attrs={"style": INPUT_STYLE}),
        }


class ComposerTermsForm(forms.Form):
    """Form for setting sponsorship terms in the composer wizard."""

    fee = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={"style": INPUT_STYLE, "placeholder": "Sponsorship fee in USD"}),
        label="Sponsorship Fee (USD)",
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
        label="Start Date",
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "style": INPUT_STYLE}),
        label="End Date",
    )
    renewal = forms.BooleanField(
        required=False,
        label="Renewal",
        help_text="Use renewal contract template instead of new sponsorship template.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 4, "style": INPUT_STYLE + "resize:vertical;", "placeholder": "Internal notes..."}
        ),
        label="Notes",
    )

    def clean(self):
        """Validate that end date is after start date."""
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end <= start:
            msg = "End date must be after start date."
            raise forms.ValidationError(msg)
        return cleaned


class LegalClauseForm(forms.ModelForm):
    """Form for creating and editing legal clauses."""

    class Meta:
        """Meta options."""

        model = LegalClause
        fields = ["internal_name", "clause", "notes"]
        widgets = {
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "clause": forms.Textarea(attrs={"rows": 6, "style": INPUT_STYLE + "resize:vertical;"}),
            "notes": forms.Textarea(
                attrs={"rows": 3, "style": INPUT_STYLE + "resize:vertical;", "placeholder": "Internal notes..."}
            ),
        }


# Dispatcher mapping config type slugs to (model, form) tuples
CONFIG_TYPES = {
    "logo_placement": (LogoPlacementConfiguration, LogoPlacementConfigForm, "Logo Placement"),
    "tiered_benefit": (TieredBenefitConfiguration, TieredBenefitConfigForm, "Tiered Benefit"),
    "email_targetable": (EmailTargetableConfiguration, EmailTargetableConfigForm, "Email Targetable"),
    "required_image": (RequiredImgAssetConfiguration, RequiredImgAssetConfigForm, "Required Image Asset"),
    "required_text": (RequiredTextAssetConfiguration, RequiredTextAssetConfigForm, "Required Text Asset"),
    "required_response": (
        RequiredResponseAssetConfiguration,
        RequiredResponseAssetConfigForm,
        "Required Response Asset",
    ),
    "provided_text": (ProvidedTextAssetConfiguration, ProvidedTextAssetConfigForm, "Provided Text Asset"),
    "provided_file": (ProvidedFileAssetConfiguration, ProvidedFileAssetConfigForm, "Provided File Asset"),
}
