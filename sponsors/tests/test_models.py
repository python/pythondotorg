from datetime import date
from model_bakery import baker

from django.test import TestCase

from ..models import Sponsor, SponsorshipBenefit, Sponsorship


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


class SponsorshipModelTests(TestCase):
    def test_create_new_sponsorship(self):
        benefits = baker.make(SponsorshipBenefit, _quantity=5, _fill_optional=True)
        info = baker.make("sponsors.SponsorInformation")

        sponsorship = Sponsorship.new(info, benefits)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.sponsor_info, info)
        self.assertEqual(sponsorship.applied_on, date.today())
        self.assertIsNone(sponsorship.approved_on)
        self.assertIsNone(sponsorship.start_date)
        self.assertIsNone(sponsorship.end_date)
        self.assertEqual(sponsorship.level_name, "")
        self.assertIsNone(sponsorship.sponsorship_fee)

        self.assertEqual(sponsorship.benefits.count(), len(benefits))
        for benefit in benefits:
            sponsor_benefit = sponsorship.benefits.get(sponsorship_benefit=benefit)
            self.assertEqual(sponsor_benefit.name, benefit.name)
            self.assertEqual(sponsor_benefit.description, benefit.description)
            self.assertEqual(sponsor_benefit.program, benefit.program)

    def test_create_new_sponsorship_with_package(self):
        benefits = baker.make(SponsorshipBenefit, _quantity=5, _fill_optional=True)
        package = baker.make(
            "sponsors.SponsorshipPackage",
            name="PSF Sponsorship Program",
            sponsorship_amount=100,
        )
        info = baker.make("sponsors.SponsorInformation")

        sponsorship = Sponsorship.new(info, benefits, package=package)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.level_name, "PSF Sponsorship Program")
        self.assertEqual(sponsorship.sponsorship_fee, 100)
