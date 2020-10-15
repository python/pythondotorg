from django import forms
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from sponsors.models import SponsorshipBenefit, SponsorshipLevel, SponsorshipProgram



class SponsorshiptBenefitsForm(forms.Form):
    levels = forms.ModelChoiceField(
        queryset=SponsorshipLevel.objects.all(),
        widget=forms.RadioSelect(), required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        benefits_qs = SponsorshipBenefit.objects.select_related("program", "minimum_level")
        for program in SponsorshipProgram.objects.all():
            slug = slugify(program.name).replace("-", "_")
            self.fields[f"benefits_{slug}"] = forms.ModelMultipleChoiceField(
                queryset=benefits_qs.filter(program=program),
                widget=forms.CheckboxSelectMultiple(), required=False,
                label=_(f"{program.name} Sponsorship Benefits")
            )

    @property
    def benefits_programs(self):
        return [f for f in self if f.name.startswith("benefits_")]

    def clean(self):
        cleaned_data = super().clean()

        if not any([cleaned_data.get(bp.name) for bp in self.benefits_programs]):
            raise forms.ValidationError(_("You have to pick a minimum number of benefits."))

        return cleaned_data
