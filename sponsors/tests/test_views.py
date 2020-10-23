from model_bakery import baker
from django.urls import reverse, reverse_lazy
from django.test import TestCase

from ..models import Sponsor, SponsorshipProgram, SponsorshipBenefit
from companies.models import Company

from sponsors.forms import SponsorshiptBenefitsForm


class SponsorViewTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Python")

        self.Sponsor1 = Sponsor.objects.create(company=self.company1, is_published=True)

        self.company2 = Company.objects.create(name="Python Hidden")

        self.Sponsor2 = Sponsor.objects.create(
            company=self.company2, is_published=False
        )

    def test_sponsor_list(self):
        url = reverse("sponsor_list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["sponsors"]), 1)


class NewSponsorshipApplicationViewTests(TestCase):
    # TODO unit test post behavior
    url = reverse_lazy("new_sponsorship_application")

    def setUp(self):
        self.psf = baker.make("sponsors.SponsorshipProgram", name="PSF")
        self.wk = baker.make("sponsors.SponsorshipProgram", name="Working Group")
        self.program_1_benefits = baker.make(
            SponsorshipBenefit, program=self.psf, _quantity=3
        )
        self.program_2_benefits = baker.make(
            SponsorshipBenefit, program=self.wk, _quantity=5
        )

    def test_display_template_with_form_and_context(self):
        psf_package = baker.make("sponsors.SponsorshipPackage")
        extra_package = baker.make("sponsors.SponsorshipPackage")

        r = self.client.get(self.url)
        packages = r.context["sponsorship_packages"]

        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "sponsors/sponsorship_benefits_form.html")
        self.assertIsInstance(r.context["form"], SponsorshiptBenefitsForm)
        self.assertEqual(r.context["benefit_model"], SponsorshipBenefit)
        self.assertEqual(2, packages.count())
        self.assertIn(psf_package, packages)
        self.assertIn(extra_package, packages)
