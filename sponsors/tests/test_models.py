from model_bakery import baker

from django.test import TestCase

from ..models import Sponsor, SponsorshipBenefit
from companies.models import Company


class SponsorModelTests(TestCase):
    def setUp(self):
        self.company1 = Company.objects.create(name="Python")

        self.Sponsor1 = Sponsor.objects.create(company=self.company1, is_published=True)

        self.company2 = Company.objects.create(name="Python Hidden")

        self.Sponsor2 = Sponsor.objects.create(
            company=self.company2, is_published=False
        )

    def test_draft(self):
        self.assertQuerysetEqual(Sponsor.objects.draft(), ["<Sponsor: Python Hidden>"])

    def test_published(self):
        self.assertQuerysetEqual(Sponsor.objects.published(), ["<Sponsor: Python>"])

    def test_featured(self):
        self.company3 = Company.objects.create(name="Python Featured")

        self.Sponsor3 = Sponsor.objects.create(
            company=self.company3, is_published=True, featured=True
        )

        self.assertQuerysetEqual(
            Sponsor.objects.featured(), ["<Sponsor: Python Featured>"]
        )


class SponsorshipBenefitModelTests(TestCase):
    def test_with_conflicts(self):
        benefit_1, benefit_2, benefit_3 = baker.make(SponsorshipBenefit, _quantity=3)
        benefit_1.conflicts.add(benefit_2)

        qs = SponsorshipBenefit.objects.with_conflicts()

        self.assertEqual(2, qs.count())
        self.assertIn(benefit_1, qs)
        self.assertIn(benefit_2, qs)

    def test_has_capacity(self):
        benefit = baker.prepare(SponsorshipBenefit, capacity=10, soft_capacity=False)
        self.assertTrue(benefit.has_capacity)
        benefit.capacity = 0
        self.assertFalse(benefit.has_capacity)
        benefit.soft_capacity = True
        self.assertTrue(benefit.has_capacity)


class SponsorshipPackageModelTests(TestCase):
    def setUp(self):
        self.package = baker.make("sponsors.SponsorshipPackage")

    def test_cost_calc(self):
        baker.make(SponsorshipBenefit, internal_value=None)
        baker.make(SponsorshipBenefit, internal_value=0)
        baker.make(SponsorshipBenefit, internal_value=10, _quantity=3)
        self.package.benefits.add(*SponsorshipBenefit.objects.all())

        self.assertEqual(30, self.package.cost)
