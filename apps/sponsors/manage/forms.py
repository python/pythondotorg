"""Forms for the sponsor management UI."""

import contextlib

from django import forms
from django.utils import timezone

from apps.sponsors.models import (
    SPONSOR_TEMPLATE_HELP_TEXT,
    EmailTargetableConfiguration,
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

MIN_YEAR = 2022
MAX_YEAR = 2050


def year_choices():
    """Return year choices for select widgets."""
    current = timezone.now().year
    return [(y, str(y)) for y in range(current + 2, 2021, -1)]


class SponsorshipBenefitManageForm(forms.ModelForm):
    """Form for creating and editing sponsorship benefits."""

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
            "packages": forms.CheckboxSelectMultiple(),
            "year": forms.Select(
                attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"}
            ),
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with year choices and package filtering."""
        super().__init__(*args, **kwargs)
        self.fields["year"].widget = forms.Select(
            choices=[("", "---"), *year_choices()],
            attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"},
        )
        # Filter packages to benefit's year, or initial year, or current year
        filter_year = None
        if self.instance and self.instance.year:
            filter_year = self.instance.year
        elif self.initial.get("year"):
            filter_year = self.initial["year"]
        else:
            with contextlib.suppress(SponsorshipCurrentYear.DoesNotExist):
                filter_year = SponsorshipCurrentYear.get_year()
        if filter_year:
            self.fields["packages"].queryset = SponsorshipPackage.objects.filter(year=filter_year).order_by(
                "-sponsorship_amount"
            )


class SponsorshipPackageManageForm(forms.ModelForm):
    """Form for creating and editing sponsorship packages."""

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
        """Initialize form with year choices."""
        super().__init__(*args, **kwargs)
        self.fields["year"].widget = forms.Select(
            choices=[("", "---"), *year_choices()],
            attrs={"style": "padding:8px 12px;border:1px solid #ccc;border-radius:4px;font-size:14px;"},
        )


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
        if year < MIN_YEAR or year > MAX_YEAR:
            msg = f"Year must be between {MIN_YEAR} and {MAX_YEAR}."
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
        if selected_year:
            self.fields["package"].queryset = SponsorshipPackage.objects.filter(year=selected_year)
        else:
            self.fields["package"].queryset = SponsorshipPackage.objects.all()


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
        if self.instance and self.instance.year:
            self.fields["package"].queryset = SponsorshipPackage.objects.filter(year=self.instance.year).order_by(
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
        help_text="Upload the final version of the signed contract (PDF or DOCX).",
        widget=forms.ClearableFileInput(attrs={"style": INPUT_STYLE, "accept": ".pdf,.docx"}),
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

    def __init__(self, *args, **kwargs):
        """Initialize form with year-filtered packages."""
        super().__init__(*args, **kwargs)
        # Filter packages to the sponsorship's year
        if self.instance and self.instance.year:
            self.fields["package"].queryset = SponsorshipPackage.objects.filter(year=self.instance.year).order_by(
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
        help_text="Upload the signed PDF.",
        widget=forms.ClearableFileInput(attrs={"style": INPUT_STYLE, "accept": ".pdf,.docx"}),
    )


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


class LogoPlacementConfigForm(forms.ModelForm):
    """Form for LogoPlacementConfiguration."""

    class Meta:
        """Meta options."""

        model = LogoPlacementConfiguration
        fields = ["publisher", "logo_place", "link_to_sponsors_page", "describe_as_sponsor"]
        widgets = {
            "publisher": forms.Select(attrs={"style": INPUT_STYLE}),
            "logo_place": forms.Select(attrs={"style": INPUT_STYLE}),
        }


class TieredBenefitConfigForm(forms.ModelForm):
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


class EmailTargetableConfigForm(forms.ModelForm):
    """Form for EmailTargetableConfiguration (no extra fields)."""

    class Meta:
        """Meta options."""

        model = EmailTargetableConfiguration
        fields = []


class RequiredImgAssetConfigForm(forms.ModelForm):
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


class RequiredTextAssetConfigForm(forms.ModelForm):
    """Form for RequiredTextAssetConfiguration."""

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
            "max_length": forms.NumberInput(attrs={"style": INPUT_STYLE}),
        }


class RequiredResponseAssetConfigForm(forms.ModelForm):
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


class ProvidedTextAssetConfigForm(forms.ModelForm):
    """Form for ProvidedTextAssetConfiguration."""

    class Meta:
        """Meta options."""

        model = ProvidedTextAssetConfiguration
        fields = ["related_to", "internal_name", "label", "help_text", "shared"]
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
        }


class ProvidedFileAssetConfigForm(forms.ModelForm):
    """Form for ProvidedFileAssetConfiguration."""

    class Meta:
        """Meta options."""

        model = ProvidedFileAssetConfiguration
        fields = ["related_to", "internal_name", "label", "help_text", "shared"]
        widgets = {
            "related_to": forms.Select(attrs={"style": INPUT_STYLE}),
            "internal_name": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "label": forms.TextInput(attrs={"style": INPUT_STYLE}),
            "help_text": forms.TextInput(attrs={"style": INPUT_STYLE}),
        }


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
