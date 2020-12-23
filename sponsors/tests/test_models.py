from datetime import date
from model_bakery import baker

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from ..models import Sponsor, SponsorshipBenefit, Sponsorship
from ..exceptions import (
    SponsorWithExistingApplicationException,
    SponsorshipInvalidStatusException,
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
        self.user = baker.make(settings.AUTH_USER_MODEL)

    def test_control_sponsorship_next_status(self):
        states_map = {
            Sponsorship.APPLIED: [Sponsorship.APPROVED, Sponsorship.REJECTED],
            Sponsorship.APPROVED: [Sponsorship.FINALIZED],
            Sponsorship.REJECTED: [],
            Sponsorship.FINALIZED: [],
        }
        for status, exepcted in states_map.items():
            sponsorship = baker.prepare(Sponsorship, status=status)
            self.assertEqual(sponsorship.next_status, exepcted)

    def test_create_new_sponsorship(self):
        sponsorship = Sponsorship.new(
            self.sponsor, self.benefits, submited_by=self.user
        )
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.submited_by, self.user)
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
            self.assertTrue(sponsor_benefit.added_by_user)
            self.assertEqual(sponsor_benefit.name, benefit.name)
            self.assertEqual(sponsor_benefit.description, benefit.description)
            self.assertEqual(sponsor_benefit.program, benefit.program)
            self.assertEqual(
                sponsor_benefit.benefit_internal_value, benefit.internal_value
            )

    def test_create_new_sponsorship_with_package(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits, package=self.package)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.level_name, "PSF Sponsorship Program")
        self.assertEqual(sponsorship.sponsorship_fee, 100)
        self.assertFalse(sponsorship.for_modified_package)
        for benefit in sponsorship.benefits.all():
            self.assertFalse(benefit.added_by_user)

    def test_create_new_sponsorship_with_package_modifications(self):
        benefits = self.benefits[:2]
        sponsorship = Sponsorship.new(self.sponsor, benefits, package=self.package)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertTrue(sponsorship.for_modified_package)
        self.assertEqual(sponsorship.benefits.count(), 2)
        for benefit in sponsorship.benefits.all():
            self.assertFalse(benefit.added_by_user)

    def test_create_new_sponsorship_with_package_added_benefit(self):
        extra_benefit = baker.make(SponsorshipBenefit)
        benefits = self.benefits + [extra_benefit]
        sponsorship = Sponsorship.new(self.sponsor, benefits, package=self.package)
        sponsorship.refresh_from_db()

        self.assertTrue(sponsorship.for_modified_package)
        self.assertEqual(sponsorship.benefits.count(), 6)
        for benefit in self.benefits:
            sponsor_benefit = sponsorship.benefits.get(sponsorship_benefit=benefit)
            self.assertFalse(sponsor_benefit.added_by_user)
            self.assertIn(sponsor_benefit, sponsorship.package_benefits)
        sponsor_benefit = sponsorship.benefits.get(sponsorship_benefit=extra_benefit)
        self.assertTrue(sponsor_benefit.added_by_user)
        self.assertEqual([sponsor_benefit], list(sponsorship.added_benefits))

    def test_estimated_cost_property(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        estimated_cost = sum([b.internal_value for b in self.benefits])

        self.assertNotEqual(estimated_cost, 0)
        self.assertEqual(estimated_cost, sponsorship.estimated_cost)

        # estimated cost should not change even if original benefts get update
        SponsorshipBenefit.objects.all().update(internal_value=0)
        self.assertEqual(estimated_cost, sponsorship.estimated_cost)

    def test_approve_sponsorship(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        self.assertEqual(sponsorship.status, Sponsorship.APPLIED)
        self.assertIsNone(sponsorship.approved_on)

        sponsorship.approve()

        self.assertEqual(sponsorship.status, Sponsorship.APPROVED)
        self.assertEqual(sponsorship.approved_on, timezone.now().date())

    def test_rollback_sponsorship_to_edit(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        can_rollback_from = [
            Sponsorship.APPLIED,
            Sponsorship.APPROVED,
            Sponsorship.REJECTED,
        ]
        for status in can_rollback_from:
            sponsorship.status = status
            sponsorship.save()
            sponsorship.refresh_from_db()

            sponsorship.rollback_to_editing()

            self.assertEqual(sponsorship.status, Sponsorship.APPLIED)
            self.assertIsNone(sponsorship.approved_on)
            self.assertIsNone(sponsorship.rejected_on)

        sponsorship.status = Sponsorship.FINALIZED
        sponsorship.save()
        sponsorship.refresh_from_db()
        with self.assertRaises(SponsorshipInvalidStatusException):
            sponsorship.rollback_to_editing()

    def test_raise_exception_when_trying_to_create_sponsorship_for_same_sponsor(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        finalized_status = [Sponsorship.REJECTED, Sponsorship.FINALIZED]
        for status in finalized_status:
            sponsorship.status = status
            sponsorship.save()

            new_sponsorship = Sponsorship.new(self.sponsor, self.benefits)
            new_sponsorship.refresh_from_db()
            self.assertTrue(new_sponsorship.pk)
            new_sponsorship.delete()

        pending_status = [Sponsorship.APPLIED, Sponsorship.APPROVED]
        for status in pending_status:
            sponsorship.status = status
            sponsorship.save()

            with self.assertRaises(SponsorWithExistingApplicationException):
                Sponsorship.new(self.sponsor, self.benefits)


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
