from itertools import chain
from django import forms
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from sponsors.models import (
    SponsorshipBenefit,
    SponsorshipPackage,
    SponsorshipProgram,
    SponsorInformation,
    SponsorContact,
)


class PickSponsorshipBenefitsField(forms.ModelMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def label_from_instance(self, obj):
        return obj.name


class SponsorshiptBenefitsForm(forms.Form):
    package = forms.ModelChoiceField(
        queryset=SponsorshipPackage.objects.all(),
        widget=forms.RadioSelect(),
        required=False,
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        benefits_qs = SponsorshipBenefit.objects.select_related("program")
        for program in SponsorshipProgram.objects.all():
            slug = slugify(program.name).replace("-", "_")
            self.fields[f"benefits_{slug}"] = PickSponsorshipBenefitsField(
                queryset=benefits_qs.filter(program=program),
                required=False,
                label=_(f"{program.name} Sponsorship Benefits"),
            )

    @property
    def benefits_programs(self):
        return [f for f in self if f.name.startswith("benefits_")]

    @property
    def benefits_conflicts(self):
        """
        Returns a dict with benefits ids as keys and their list of conlicts ids as values
        """
        conflicts = {}
        for benefit in SponsorshipBenefit.objects.with_conflicts():
            benefits_conflicts = benefit.conflicts.values_list("id", flat=True)
            if benefits_conflicts:
                conflicts[benefit.id] = list(benefits_conflicts)
        return conflicts

    def get_benefits(self, cleaned_data=None):
        cleaned_data = cleaned_data or self.cleaned_data
        return list(
            chain(*(cleaned_data.get(bp.name) for bp in self.benefits_programs))
        )

    def _clean_benefits(self, cleaned_data):
        """
        Validate chosen benefits. Invalid scenarios are:
        - benefits with conflits
        - package only benefits and form without SponsorshipProgram
        - benefit with no capacity, except if soft
        """
        package = cleaned_data.get("package")
        benefits = self.get_benefits(cleaned_data)
        if not benefits:
            raise forms.ValidationError(
                _("You have to pick a minimum number of benefits.")
            )

        benefits_ids = [b.id for b in benefits]
        for benefit in benefits:
            conflicts = set(self.benefits_conflicts.get(benefit.id, []))
            if conflicts and set(benefits_ids).intersection(conflicts):
                raise forms.ValidationError(
                    _("The application has 1 or more benefits that conflicts.")
                )

            if benefit.package_only:
                if not package:
                    raise forms.ValidationError(
                        _(
                            "The application has 1 or more package only benefits and no package."
                        )
                    )
                elif not benefit.packages.filter(id=package.id).exists():
                    raise forms.ValidationError(
                        _(
                            "The application has 1 or more package only benefits but wrong package."
                        )
                    )

            if not benefit.has_capacity:
                raise forms.ValidationError(
                    _("The application has 1 or more benefits with no capacity.")
                )

        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()
        return self._clean_benefits(cleaned_data)


class SponsorshipApplicationForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Sponsor name",
        help_text="Name of the sponsor, for public display.",
    )
    description = forms.CharField(
        label="Sponsor description",
        help_text="Brief description of the sponsor for public display.",
        required=False,
        widget=forms.TextInput,
    )
    landing_page_url = forms.URLField(
        label="Sponsor landing page",
        help_text="Sponsor landing page URL. This may be provided by the sponsor, however the linked page may not contain any sales or marketing information.",
        required=False,
    )
    web_logo = forms.ImageField(
        label="Sponsor web logo",
        help_text="For display on our sponsor webpage. High resolution PNG or JPG, smallest dimension no less than 256px",
    )
    print_logo = forms.FileField(
        label="Sponsor print logo",
        help_text="For printed materials, signage, and projection. SVG or EPS",
        required=False,
    )

    primary_phone = forms.CharField(label="Sponsor Primary Phone", max_length=32)
    mailing_address = forms.CharField(
        label="Sponsor Mailing/Billing Address", widget=forms.TextInput
    )

    # contact information
    contact_name = forms.CharField(max_length=100)
    contact_email = forms.EmailField(max_length=256)
    contact_phone = forms.CharField(label="Contact Phone", max_length=32)

    def save(self):
        sponsor_info = SponsorInformation.objects.create(
            name=self.cleaned_data["name"],
            web_logo=self.cleaned_data["web_logo"],
            primary_phone=self.cleaned_data["primary_phone"],
            mailing_address=self.cleaned_data["mailing_address"],
            description=self.cleaned_data.get("description", ""),
            landing_page_url=self.cleaned_data.get("landing_page_url", ""),
            print_logo=self.cleaned_data.get("print_logo"),
        )
        SponsorContact.objects.create(
            sponsor=sponsor_info,
            name=self.cleaned_data["contact_name"],
            phone=self.cleaned_data["contact_phone"],
            email=self.cleaned_data["contact_email"],
        )
        return sponsor_info
