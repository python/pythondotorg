from django import forms

from sponsors.models import SponsorshipBenefit, SponsorshipLevel


class SponsorshiptBenefitsForm(forms.Form):
    levels = forms.ModelChoiceField(
        queryset=SponsorshipLevel.objects.all(),
        widget=forms.RadioSelect(), required=False,
    )
    benefits = forms.ModelMultipleChoiceField(
        queryset=SponsorshipBenefit.objects.select_related("program", "minimum_level"),
        widget=forms.CheckboxSelectMultiple(), required=True,
    )
