from model_bakery import baker
from django.test import TestCase

from sponsors.forms import SponsorshiptBenefitsForm
from sponsors.models import SponsorshipBenefit


class SponsorshiptBenefitsFormTests(TestCase):
    def setUp(self):
        self.psf = baker.make("sponsors.SponsorshipProgram", name="PSF")
        self.wk = baker.make("sponsors.SponsorshipProgram", name="Working Group")
        self.program_1_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3
        )
        self.program_2_benefits = baker.make(
            SponsorshipBenefit, program=self.wk, _quantity=5
        )

    def test_benefits_organized_by_program(self):
        form = SponsorshiptBenefitsForm()

        field1, field2 = sorted(form.benefits_programs, key=lambda f: f.name)

        self.assertEqual("benefits_psf", field1.name)
        self.assertEqual("PSF Sponsorship Benefits", field1.label)
        choices = list(field1.field.choices)
        self.assertEqual(len(self.program_1_benefits), len(choices))
        for benefit in self.program_1_benefits:
            self.assertIn(benefit.id, [c[0] for c in choices])

        self.assertEqual("benefits_working_group", field2.name)
        self.assertEqual("Working Group Sponsorship Benefits", field2.label)
        choices = list(field2.field.choices)
        self.assertEqual(len(self.program_2_benefits), len(choices))
        for benefit in self.program_2_benefits:
            self.assertIn(benefit.id, [c[0] for c in choices])

    def test_invalidate_form_without_benefits(self):
        form = SponsorshiptBenefitsForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

        form = SponsorshiptBenefitsForm(
            data={"benefits_psf": [self.program_1_benefits[0].id]}
        )
        self.assertTrue(form.is_valid())
