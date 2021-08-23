from itertools import chain
from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminDateWidget
from django.db.models import Q
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField

from sponsors.models import (
    SponsorshipBenefit,
    SponsorshipPackage,
    SponsorshipProgram,
    Sponsor,
    SponsorContact,
    Sponsorship,
    SponsorBenefit,
)


class PickSponsorshipBenefitsField(forms.ModelMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def label_from_instance(self, obj):
        return obj.name


class SponsorContactForm(forms.ModelForm):
    class Meta:
        model = SponsorContact
        fields = ["name", "email", "phone", "primary", "administrative", "accounting"]


SponsorContactFormSet = forms.formset_factory(
    SponsorContactForm,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=False,
    can_order=False,
    max_num=5,
)


class SponsorshiptBenefitsForm(forms.Form):
    package = forms.ModelChoiceField(
        queryset=SponsorshipPackage.objects.all(),
        widget=forms.RadioSelect(),
        required=False,
        empty_label=None,
    )
    add_ons_benefits = PickSponsorshipBenefitsField(
        required=False,
        queryset=SponsorshipBenefit.objects.add_ons().select_related("program"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        benefits_qs = SponsorshipBenefit.objects.with_packages().select_related(
            "program"
        )

        for program in SponsorshipProgram.objects.all():
            slug = slugify(program.name).replace("-", "_")
            self.fields[f"benefits_{slug}"] = PickSponsorshipBenefitsField(
                queryset=benefits_qs.filter(program=program),
                required=False,
                label=_("{program_name} Benefits").format(program_name=program.name),
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

    def get_package(self):
        return self.cleaned_data.get("package")

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
                            "The application has 1 or more package only benefits and no sponsor package."
                        )
                    )
                elif not benefit.packages.filter(id=package.id).exists():
                    raise forms.ValidationError(
                        _(
                            "The application has 1 or more package only benefits but wrong sponsor package."
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
        required=False,
    )
    description = forms.CharField(
        label="Sponsor description",
        help_text="Brief description of the sponsor for public display.",
        required=False,
        widget=forms.TextInput,
    )
    landing_page_url = forms.URLField(
        label="Sponsor landing page",
        help_text="Landing page URL. The linked page may not contain any sales or marketing information.",
        required=False,
    )
    twitter_handle = forms.CharField(
        max_length=32,
        label="Twitter handle",
        help_text="For promotion of your sponsorship on social media.",
        required=False,
    )
    web_logo = forms.ImageField(
        label="Sponsor web logo",
        help_text="For display on our sponsor webpage. High resolution PNG or JPG, smallest dimension no less than 256px",
        required=False,
    )
    print_logo = forms.FileField(
        label="Sponsor print logo",
        help_text="For printed materials, signage, and projection. SVG or EPS",
        required=False,
    )

    primary_phone = forms.CharField(
        label="Sponsor Primary Phone",
        max_length=32,
        required=False,
    )
    mailing_address_line_1 = forms.CharField(
        label="Mailing Address line 1",
        widget=forms.TextInput,
        required=False,
    )
    mailing_address_line_2 = forms.CharField(
        label="Mailing Address line 2",
        widget=forms.TextInput,
        required=False,
    )

    city = forms.CharField(max_length=64, required=False)
    state = forms.CharField(
        label="State/Province/Region", max_length=64, required=False
    )
    postal_code = forms.CharField(
        label="Zip/Postal Code", max_length=64, required=False
    )
    country = CountryField().formfield(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        qs = Sponsor.objects.none()
        if self.user:
            sponsor_ids = SponsorContact.objects.filter(user=self.user).values_list(
                "sponsor", flat=True
            )
            qs = Sponsor.objects.filter(id__in=sponsor_ids)
        self.fields["sponsor"] = forms.ModelChoiceField(queryset=qs, required=False)

        formset_kwargs = {"prefix": "contact"}
        if self.data:
            self.contacts_formset = SponsorContactFormSet(self.data, **formset_kwargs)
        else:
            self.contacts_formset = SponsorContactFormSet(**formset_kwargs)

    def clean(self):
        cleaned_data = super().clean()
        sponsor = self.data.get("sponsor")
        if not sponsor and not self.contacts_formset.is_valid():
            msg = "Errors with contact(s) information"
            if not self.contacts_formset.errors:
                msg = "You have to enter at least one contact"
            raise forms.ValidationError(msg)
        elif not sponsor:
            has_primary_contact = any(
                f.cleaned_data.get("primary") for f in self.contacts_formset.forms
            )
            if not has_primary_contact:
                msg = "You have to mark at least one contact as the primary one."
                raise forms.ValidationError(msg)

    def clean_sponsor(self):
        sponsor = self.cleaned_data.get("sponsor")
        if not sponsor:
            return

        if Sponsorship.objects.in_progress().filter(sponsor=sponsor).exists():
            msg = f"The sponsor {sponsor.name} already have open Sponsorship applications. "
            msg += f"Get in contact with {settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL} to discuss."
            raise forms.ValidationError(msg)

        return sponsor

    # Required fields are being manually validated because if the form
    # data has a Sponsor they shouldn't be required
    def clean_name(self):
        name = self.cleaned_data.get("name", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not name:
            raise forms.ValidationError("This field is required.")
        return name.strip()

    def clean_web_logo(self):
        web_logo = self.cleaned_data.get("web_logo", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not web_logo:
            raise forms.ValidationError("This field is required.")
        return web_logo

    def clean_primary_phone(self):
        primary_phone = self.cleaned_data.get("primary_phone", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not primary_phone:
            raise forms.ValidationError("This field is required.")
        return primary_phone.strip()

    def clean_mailing_address_line_1(self):
        mailing_address_line_1 = self.cleaned_data.get("mailing_address_line_1", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not mailing_address_line_1:
            raise forms.ValidationError("This field is required.")
        return mailing_address_line_1.strip()

    def clean_city(self):
        city = self.cleaned_data.get("city", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not city:
            raise forms.ValidationError("This field is required.")
        return city.strip()

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get("postal_code", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not postal_code:
            raise forms.ValidationError("This field is required.")
        return postal_code.strip()

    def clean_country(self):
        country = self.cleaned_data.get("country", "")
        sponsor = self.data.get("sponsor")
        if not sponsor and not country:
            raise forms.ValidationError("This field is required.")
        return country.strip()

    def save(self):
        selected_sponsor = self.cleaned_data.get("sponsor")
        if selected_sponsor:
            return selected_sponsor

        sponsor = Sponsor.objects.create(
            name=self.cleaned_data["name"],
            web_logo=self.cleaned_data["web_logo"],
            primary_phone=self.cleaned_data["primary_phone"],
            mailing_address_line_1=self.cleaned_data["mailing_address_line_1"],
            mailing_address_line_2=self.cleaned_data.get("mailing_address_line_2", ""),
            city=self.cleaned_data["city"],
            state=self.cleaned_data.get("state", ""),
            postal_code=self.cleaned_data["postal_code"],
            country=self.cleaned_data["country"],
            description=self.cleaned_data.get("description", ""),
            landing_page_url=self.cleaned_data.get("landing_page_url", ""),
            twitter_handle=self.cleaned_data["twitter_handle"],
            print_logo=self.cleaned_data.get("print_logo"),
        )
        contacts = [f.save(commit=False) for f in self.contacts_formset.forms]
        for contact in contacts:
            if self.user and self.user.email.lower() == contact.email.lower():
                contact.user = self.user
            contact.sponsor = sponsor
            contact.save()

        return sponsor

    @cached_property
    def user_with_previous_sponsors(self):
        if not self.user:
            return False
        return self.fields["sponsor"].queryset.exists()


class SponsorshipReviewAdminForm(forms.ModelForm):
    start_date = forms.DateField(widget=AdminDateWidget(), required=False)
    end_date = forms.DateField(widget=AdminDateWidget(), required=False)

    def __init__(self, *args, **kwargs):
        force_required = kwargs.pop("force_required", False)
        super().__init__(*args, **kwargs)
        if force_required:
            for field_name in self.fields:
                self.fields[field_name].required = True

    class Meta:
        model = Sponsorship
        fields = ["start_date", "end_date", "level_name", "sponsorship_fee"]

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date <= start_date:
            raise forms.ValidationError("End date must be greater than start date")

        return cleaned_data


class SponsorBenefitAdminInlineForm(forms.ModelForm):
    sponsorship_benefit = forms.ModelChoiceField(
        queryset=SponsorshipBenefit.objects.order_by('program', 'order').select_related("program"),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "benefit_internal_value" in self.fields:
            self.fields["benefit_internal_value"].required = True

    class Meta:
        model = SponsorBenefit
        fields = ["sponsorship_benefit", "sponsorship", "benefit_internal_value"]

    def save(self, commit=True):
        sponsorship = self.cleaned_data["sponsorship"]
        benefit = self.cleaned_data["sponsorship_benefit"]
        value = self.cleaned_data["benefit_internal_value"]

        if not (self.instance and self.instance.pk):  # new benefit
            self.instance = SponsorBenefit(sponsorship=sponsorship)
        else:
            self.instance.refresh_from_db()

        self.instance.benefit_internal_value = value
        if benefit.pk != self.instance.sponsorship_benefit_id:
            self.instance.sponsorship_benefit = benefit
            self.instance.name = benefit.name
            self.instance.description = benefit.description
            self.instance.program = benefit.program

        if commit:
            self.instance.save()

        return self.instance


class SponsorshipsListForm(forms.Form):
    sponsorships = forms.ModelMultipleChoiceField(
        required=True,
        queryset=Sponsorship.objects.select_related("sponsor"),
        widget=forms.CheckboxSelectMultiple,
    )

    @classmethod
    def with_benefit(cls, sponsorship_benefit, *args, **kwargs):
        """
        Queryset considering only valid sponsorships which have the benefit
        """
        today = timezone.now().date()
        queryset = sponsorship_benefit.related_sponsorships.exclude(
            Q(end_date__lt=today) | Q(status=Sponsorship.REJECTED)
        ).select_related("sponsor")

        form = cls(*args, **kwargs)
        form.fields["sponsorships"].queryset = queryset
        form.sponsorship_benefit = sponsorship_benefit

        return form
