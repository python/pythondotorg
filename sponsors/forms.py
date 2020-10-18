from itertools import chain
from django import forms
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from sponsors.models import SponsorshipBenefit, SponsorshipPackage, SponsorshipProgram


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
            self.fields[f"benefits_{slug}"] = forms.ModelMultipleChoiceField(
                queryset=benefits_qs.filter(program=program),
                widget=forms.CheckboxSelectMultiple(),
                required=False,
                label=_(f"{program.name} Sponsorship Benefits"),
            )

    @property
    def benefits_programs(self):
        return [f for f in self if f.name.startswith("benefits_")]

    @property
    def benefits_by_package(self):
        """
        Returns a dict with packages ids as keys and a list of benefits ids as values
        """
        packages_benefits = {}
        for package in SponsorshipPackage.objects.all():
            packages_benefits[package.id] = package.benefits.values_list(
                "id", flat=True
            )
        return packages_benefits

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
        return list(chain(*(cleaned_data.get(bp.name) for bp in self.benefits_programs)))

    def clean(self):
        cleaned_data = super().clean()
        benefits = self.get_benefits(cleaned_data)

        if not benefits:
            raise forms.ValidationError(
                _("You have to pick a minimum number of benefits.")
            )

        benefits = [b.id for b in benefits]
        for benefit in benefits:
            conflicts = set(self.benefits_conflicts.get(benefit, []))
            if not conflicts:
                return

            if set(benefits).intersection(conflicts):
                raise forms.ValidationError(
                    _("The application has 1 or more benefits that conflicts.")
                )

        return cleaned_data
