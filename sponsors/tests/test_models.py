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
    def setUp(self):
        self.benefits = baker.make(SponsorshipBenefit, _quantity=5, _fill_optional=True)
        self.package = baker.make(
            "sponsors.SponsorshipPackage",
            name="PSF Sponsorship Program",
            sponsorship_amount=100,
        )
        self.package.benefits.add(*self.benefits)
        self.sponsor = baker.make("sponsors.Sponsor")

    def test_create_new_sponsorship(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.sponsor, self.sponsor)
        self.assertEqual(sponsorship.applied_on, date.today())
        self.assertEqual(sponsorship.status, Sponsorship.APPLIED)
        self.assertIsNone(sponsorship.approved_on)
        self.assertIsNone(sponsorship.rejected_on)
        self.assertIsNone(sponsorship.finalized_on)
        self.assertIsNone(sponsorship.start_date)
        self.assertIsNone(sponsorship.end_date)
        self.assertEqual(sponsorship.level_name, "")
        self.assertIsNone(sponsorship.sponsorship_fee)
        self.assertTrue(sponsorship.for_modified_package)

        self.assertEqual(sponsorship.benefits.count(), len(self.benefits))
        for benefit in self.benefits:
            sponsor_benefit = sponsorship.benefits.get(sponsorship_benefit=benefit)
            self.assertEqual(sponsor_benefit.name, benefit.name)
            self.assertEqual(sponsor_benefit.description, benefit.description)
            self.assertEqual(sponsor_benefit.program, benefit.program)
            self.assertEqual(sponsor_benefit.benefit_internal_value, benefit.internal_value)

    def test_create_new_sponsorship_with_package(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits, package=self.package)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.level_name, "PSF Sponsorship Program")
        self.assertEqual(sponsorship.sponsorship_fee, 100)
        self.assertFalse(sponsorship.for_modified_package)

    def test_create_new_sponsorship_with_package_modifications(self):
        benefits = self.benefits[:2]
        sponsorship = Sponsorship.new(self.sponsor, benefits, package=self.package)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertTrue(sponsorship.for_modified_package)
        self.assertEqual(sponsorship.benefits.count(), 2)


class SponsorshipPackageTests(TestCase):
    def setUp(self):
        self.package = baker.make("sponsors.SponsorshipPackage")
        self.package_benefits = baker.make(SponsorshipBenefit, _quantity=3)
        self.package.benefits.add(*self.package_benefits)

    def test_has_user_customization_if_benefit_from_other_package(self):
        extra = baker.make(SponsorshipBenefit)
        customization = self.package.has_user_customization(
            [extra] + self.package_benefits
        )
        self.assertTrue(customization)

    def test_no_user_customization_if_all_benefits_from_package(self):
        customization = self.package.has_user_customization(self.package_benefits)
        self.assertFalse(customization)

    def test_has_user_customization_if_missing_package_benefit(self):
        self.package_benefits.pop()
        customization = self.package.has_user_customization(self.package_benefits)
        self.assertTrue(customization)

    def test_no_user_customization_if_at_least_one_of_conflicts_is_passed(self):
        benefits = baker.make(SponsorshipBenefit, _quantity=3)
        benefits[0].conflicts.add(benefits[1])
        benefits[0].conflicts.add(benefits[2])
        benefits[1].conflicts.add(benefits[2])
        self.package.benefits.add(*benefits)

        customization = self.package.has_user_customization(
            self.package_benefits + benefits[:1]
        )
        self.assertFalse(customization)

    def test_user_customization_if_missing_benefit_with_conflict(self):
        benefits = baker.make(SponsorshipBenefit, _quantity=3)
        benefits[0].conflicts.add(benefits[1])
        benefits[0].conflicts.add(benefits[2])
        benefits[1].conflicts.add(benefits[2])
        self.package.benefits.add(*benefits)

        customization = self.package.has_user_customization(self.package_benefits)
        self.assertTrue(customization)

    def test_user_customization_if_missing_benefit_with_conflict_from_one_or_more_conflicts_set(
        self,
    ):
        benefits = baker.make(SponsorshipBenefit, _quantity=4)
        # 2 sets of conflict: indexes 0 vs 1 conflicts and 2 vs 3 too
        benefits[0].conflicts.add(benefits[1])
        benefits[2].conflicts.add(benefits[3])
        self.package.benefits.add(*benefits)

        benefits = self.package_benefits + [
            benefits[0]
        ]  # missing benefits with index 2 or 3
        customization = self.package.has_user_customization(benefits)
        self.assertTrue(customization)
