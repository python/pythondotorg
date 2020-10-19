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

    def test_display_template_with_form(self):
        r = self.client.get(self.url)

        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.context["form"], SponsorshiptBenefitsForm)


class CalculateSponsorshipCost(TestCase):
    url = reverse_lazy("new_sponsorship_application_price_calc")

    def setUp(self):
        self.program = baker.make(SponsorshipProgram, name="PSF")
        self.benefits = baker.make(
            SponsorshipBenefit, program=self.program, internal_value=10, _quantity=3
        )
        self.data = {"benefits_psf": [b.id for b in self.benefits]}

    def test_sponsorship_cost(self):
        response = self.client.get(self.url, data=self.data)

        self.assertEqual(200, response.status_code)
        self.assertEqual({"cost": 30}, response.json())

    def test_bad_request_if_invalid_form(self):
        response = self.client.get(self.url, data={})

        self.assertEqual(400, response.status_code)
        self.assertIn("errors", response.json())
