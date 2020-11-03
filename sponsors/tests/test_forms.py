from model_bakery import baker

from django.test import TestCase

from sponsors.forms import SponsorshiptBenefitsForm, SponsorshipApplicationForm
from sponsors.models import SponsorshipBenefit
from .utils import get_static_image_file_as_upload


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

    def test_benefit_with_no_capacity_should_not_validate(self):
        SponsorshipBenefit.objects.all().update(capacity=0)

        data = {"benefits_psf": [self.program_1_benefits[0]]}

        form = SponsorshiptBenefitsForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "The application has 1 or more benefits with no capacity.",
            form.errors["__all__"],
        )

    def test_benefit_with_soft_capacity_should_validate(self):
        SponsorshipBenefit.objects.all().update(capacity=0, soft_capacity=True)

        data = {"benefits_psf": [self.program_1_benefits[0]]}

        form = SponsorshiptBenefitsForm(data=data)
        self.assertTrue(form.is_valid())


class SponsorshipApplicationFormTests(TestCase):
    def setUp(self):
        self.data = {
            "name": "CompanyX",
            "primary_phone": "+14141413131",
            "mailing_address": "4th street",
            "contact_name": "Bernardo",
            "contact_email": "bernardo@companyemail.com",
            "contact_phone": "+1999999999",
        }
        self.files = {
            "web_logo": get_static_image_file_as_upload("psf-logo.png", "logo.png")
        }

    def test_required_fields(self):
        required_fields = [
            "name",
            "web_logo",
            "primary_phone",
            "mailing_address",
            "contact_name",
            "contact_email",
            "contact_phone",
        ]

        form = SponsorshipApplicationForm({})

        self.assertFalse(form.is_valid())
        self.assertEqual(len(required_fields), len(form.errors))
        for required in required_fields:
            self.assertIn(required, form.errors)

    def test_create_sponsor_with_valid_data(self):
        form = SponsorshipApplicationForm(self.data, self.files)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor = form.save()

        self.assertTrue(sponsor.pk)
        self.assertEqual(sponsor.name, "CompanyX")
        self.assertTrue(sponsor.web_logo)
        self.assertEqual(sponsor.primary_phone, "+14141413131")
        self.assertEqual(sponsor.mailing_address, "4th street")
        self.assertEqual(sponsor.description, "")
        self.assertIsNone(sponsor.print_logo.name)
        self.assertEqual(sponsor.landing_page_url, "")
        contact = sponsor.contacts.get()
        self.assertEqual(contact.name, "Bernardo")
        self.assertEqual(contact.email, "bernardo@companyemail.com")
        self.assertEqual(contact.phone, "+1999999999")

    def test_create_sponsor_with_valid_data_for_non_required_inputs(
        self,
    ):
        self.data["description"] = "Important company"
        self.data["landing_page_url"] = "https://companyx.com"
        self.files["print_logo"] = get_static_image_file_as_upload(
            "psf-logo_print.png", "logo_print.png"
        )

        form = SponsorshipApplicationForm(self.data, self.files)
        self.assertTrue(form.is_valid(), form.errors)

        sponsor = form.save()

        self.assertEqual(sponsor.description, "Important company")
        self.assertTrue(sponsor.print_logo)
        self.assertEqual(sponsor.landing_page_url, "https://companyx.com")
