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

    def test_benefit_by_packages_helper_property(self):
        psf_package = baker.make("sponsors.SponsorshipPackage")
        psf_package.benefits.add(*self.program_1_benefits)

        extra_package = baker.make("sponsors.SponsorshipPackage")
        extra_benefits = baker.make("sponsors.SponsorshipBenefit", _quantity=5)
        extra_package.benefits.add(*extra_benefits)

        form = SponsorshiptBenefitsForm()
        map = form.benefits_by_package

        self.assertEqual(
            sorted(map[psf_package.id]), sorted([b.id for b in self.program_1_benefits])
        )
        self.assertEqual(
            sorted(map[extra_package.id]), sorted([b.id for b in extra_benefits])
        )

    def test_benefits_conflicts_helper_property(self):
        benefit_1, benefit_2 = baker.make("sponsors.SponsorshipBenefit", _quantity=2)
        benefit_1.conflicts.add(*self.program_1_benefits)
        benefit_2.conflicts.add(*self.program_2_benefits)

        form = SponsorshiptBenefitsForm()
        map = form.benefits_conflicts

        # conflicts are symmetrical relationships
        self.assertEqual(
            2 + len(self.program_1_benefits) + len(self.program_2_benefits), len(map)
        )
        self.assertEqual(
            sorted(map[benefit_1.id]), sorted([b.id for b in self.program_1_benefits])
        )
        self.assertEqual(
            sorted(map[benefit_2.id]), sorted([b.id for b in self.program_2_benefits])
        )
        for b in self.program_1_benefits:
            self.assertEqual(map[b.id], [benefit_1.id])
        for b in self.program_2_benefits:
            self.assertEqual(map[b.id], [benefit_2.id])

    def test_invalid_form_if_any_conflict(self):
        benefit_1 = baker.make("sponsors.SponsorshipBenefit", program=self.wk)
        benefit_1.conflicts.add(*self.program_1_benefits)

        data = {"benefits_psf": [b.id for b in self.program_1_benefits]}
        form = SponsorshiptBenefitsForm(data=data)
        self.assertTrue(form.is_valid())

        data["benefits_working_group"] = [benefit_1.id]
        form = SponsorshiptBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more benefits that conflicts.",
            form.errors["__all__"],
        )

    def test_package_only_benefit_without_package_should_not_validate(self):
        SponsorshipBenefit.objects.all().update(package_only=True)

        data = {"benefits_psf": [self.program_1_benefits[0]]}

        form = SponsorshiptBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more package only benefits and no package.",
            form.errors["__all__"],
        )

    def test_package_only_benefit_with_wrong_package_should_not_validate(self):
        SponsorshipBenefit.objects.all().update(package_only=True)
        package = baker.make("sponsors.SponsorshipPackage")
        package.benefits.add(*SponsorshipBenefit.objects.all())

        data = {
            "benefits_psf": [self.program_1_benefits[0]],
            "package": baker.make("sponsors.SponsorshipPackage").id,  # other package
        }

        form = SponsorshiptBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more package only benefits but wrong package.",
            form.errors["__all__"],
        )

        data = {
            "benefits_psf": [self.program_1_benefits[0]],
            "package": package.id,
        }
        form = SponsorshiptBenefitsForm(data=data)
        self.assertTrue(form.is_valid())
