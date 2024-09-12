from datetime import date, timedelta
import random

from django.core.cache import cache
from django.db import IntegrityError
from model_bakery import baker, seq

from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.test import TestCase
from django.utils import timezone

from ..models import (
    Contract,
    LegalClause,
    LogoPlacement,
    LogoPlacementConfiguration,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipPackage,
    TieredBenefit,
    TieredBenefitConfiguration, RequiredImgAssetConfiguration, RequiredImgAsset, ImgAsset,
    RequiredTextAssetConfiguration, RequiredTextAsset, TextAsset, SponsorshipCurrentYear
)
from ..exceptions import (
    SponsorWithExistingApplicationException,
    SponsorshipInvalidDateRangeException,
    InvalidStatusException,
)
from sponsors.models.enums import PublisherChoices, LogoPlacementChoices, AssetsRelatedTo
from ..models.benefits import RequiredAssetMixin, BaseRequiredImgAsset, BenefitFeature, BaseRequiredTextAsset, \
    EmailTargetableConfiguration


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
        benefit.capacity = 10
        benefit.soft_capacity = False
        benefit.unavailable = True
        self.assertFalse(benefit.has_capacity)

    def test_list_related_sponsorships(self):
        benefit = baker.make(SponsorshipBenefit)
        sponsor_benefit = baker.make(SponsorBenefit, sponsorship_benefit=benefit)
        other_benefit = baker.make(SponsorshipBenefit)
        baker.make(SponsorBenefit, sponsorship_benefit=other_benefit)

        with self.assertNumQueries(1):
            sponsorships = list(benefit.related_sponsorships)

        self.assertEqual(2, Sponsorship.objects.count())
        self.assertEqual(1, len(sponsorships))
        self.assertIn(sponsor_benefit.sponsorship, sponsorships)

    def test_name_for_display_without_specifying_package(self):
        benefit = baker.make(SponsorshipBenefit, name='Benefit')
        benefit_config = baker.make(
            TieredBenefitConfiguration,
            package__name='Package',
            benefit=benefit,
            quantity=10
        )

        expected_name = f"Benefit (10)"
        name = benefit.name_for_display(package=benefit_config.package)
        self.assertEqual(name, expected_name)
        self.assertTrue(benefit.has_tiers)


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
        current_year = SponsorshipCurrentYear.get_year()

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
        self.assertIsNone(sponsorship.agreed_fee)
        self.assertIsNone(sponsorship.package)
        self.assertTrue(sponsorship.for_modified_package)
        self.assertEqual(sponsorship.year, current_year)

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
        self.assertEqual(sponsorship.agreed_fee, 100)  # can display the price because there's not customizations
        self.assertFalse(sponsorship.for_modified_package)
        self.assertEqual(sponsorship.package, self.package)
        for benefit in sponsorship.benefits.all():
            self.assertFalse(benefit.added_by_user)

    def test_create_new_sponsorship_with_package_modifications(self):
        benefits = self.benefits[:2]
        sponsorship = Sponsorship.new(self.sponsor, benefits, package=self.package)
        self.assertTrue(sponsorship.pk)
        sponsorship.refresh_from_db()

        self.assertTrue(sponsorship.for_modified_package)
        self.assertEqual(sponsorship.benefits.count(), 2)
        self.assertIsNone(sponsorship.agreed_fee)  # can't display the price with customizations
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
        estimated_cost = sum(b.internal_value for b in self.benefits)

        self.assertNotEqual(estimated_cost, 0)
        self.assertEqual(estimated_cost, sponsorship.estimated_cost)

        # estimated cost should not change even if original benefts get update
        SponsorshipBenefit.objects.all().update(internal_value=0)
        self.assertEqual(estimated_cost, sponsorship.estimated_cost)

    def test_approve_sponsorship(self):
        start = date.today()
        end = start + timedelta(days=10)
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        self.assertEqual(sponsorship.status, Sponsorship.APPLIED)
        self.assertIsNone(sponsorship.approved_on)

        sponsorship.approve(start, end)

        self.assertEqual(sponsorship.approved_on, timezone.now().date())
        self.assertEqual(sponsorship.status, Sponsorship.APPROVED)
        self.assertTrue(sponsorship.start_date, start)
        self.assertTrue(sponsorship.end_date, end)

    def test_exception_if_invalid_date_range_when_approving(self):
        start = date.today()
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        self.assertEqual(sponsorship.status, Sponsorship.APPLIED)
        self.assertIsNone(sponsorship.approved_on)

        with self.assertRaises(SponsorshipInvalidDateRangeException):
            sponsorship.approve(start, start)

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
        with self.assertRaises(InvalidStatusException):
            sponsorship.rollback_to_editing()

    def test_rollback_approved_sponsorship_with_contract_should_delete_it(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        sponsorship.status = Sponsorship.APPROVED
        sponsorship.save()
        baker.make_recipe('sponsors.tests.empty_contract', sponsorship=sponsorship)

        sponsorship.rollback_to_editing()
        sponsorship.save()
        sponsorship.refresh_from_db()

        self.assertEqual(sponsorship.status, Sponsorship.APPLIED)
        self.assertEqual(0, Contract.objects.count())

    def test_can_not_rollback_sponsorship_to_edit_if_contract_was_sent(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        sponsorship.status = Sponsorship.APPROVED
        sponsorship.save()
        baker.make_recipe('sponsors.tests.awaiting_signature_contract', sponsorship=sponsorship)

        with self.assertRaises(InvalidStatusException):
            sponsorship.rollback_to_editing()

        self.assertEqual(1, Contract.objects.count())

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

    def test_display_agreed_fee_for_approved_and_finalized_status(self):
        sponsorship = Sponsorship.new(self.sponsor, self.benefits)
        sponsorship.sponsorship_fee = 2000
        sponsorship.save()

        finalized_status = [Sponsorship.APPROVED, Sponsorship.FINALIZED]
        for status in finalized_status:
            sponsorship.status = status
            sponsorship.save()

            self.assertEqual(sponsorship.agreed_fee, 2000)


class SponsorshipCurrentYearTests(TestCase):

    def test_singleton_object_is_loaded_by_default(self):
        curr_year = SponsorshipCurrentYear.objects.get()
        self.assertEqual(1, curr_year.pk)
        self.assertEqual(2022, curr_year.year)

    def test_make_sure_we_cannot_add_new_current_years(self):
        self.assertTrue(SponsorshipCurrentYear.objects.get())
        with self.assertRaises(IntegrityError) as context:
            baker.make(SponsorshipCurrentYear, id=2)

        self.assertIn("sponsorship_current_year_singleton_idx", str(context.exception))

    def test_singleton_object_cannot_be_deleted(self):
        curr_year = SponsorshipCurrentYear.objects.get()
        with self.assertRaises(IntegrityError) as context:
            curr_year.delete()

        self.assertIn("Singleton object cannot be delete. Try updating it instead.", str(context.exception))

        with self.assertRaises(IntegrityError) as context:
            SponsorshipCurrentYear.objects.all().delete()

        self.assertIn("Singleton object cannot be delete. Try updating it instead.", str(context.exception))

    def test_current_year_is_cached(self):
        # cleans cached from previous test runs
        cache.clear()

        # first time: no cache
        with self.assertNumQueries(1):
            year = SponsorshipCurrentYear.get_year()

        self.assertEqual(year, cache.get(SponsorshipCurrentYear.CACHE_KEY))
        # second time: cache hit
        with self.assertNumQueries(0):
            SponsorshipCurrentYear.get_year()

        curr_year = SponsorshipCurrentYear.objects.get()
        # update should clear cache
        curr_year.year = 2024
        curr_year.save()
        with self.assertNumQueries(1):
            self.assertEqual(2024, SponsorshipCurrentYear.get_year())

        # cleans cached for next test runs
        cache.clear()


class SponsorshipPackageTests(TestCase):
    def setUp(self):
        self.package = baker.make("sponsors.SponsorshipPackage")
        self.package_benefits = baker.make(SponsorshipBenefit, _quantity=3)
        self.package.benefits.add(*self.package_benefits)

    def test_has_user_customization_if_benefit_from_other_package(self):
        extra = baker.make(SponsorshipBenefit)
        benefits = [extra] + self.package_benefits
        has_customization = self.package.has_user_customization(benefits)
        customization = {"added_by_user": {extra}, "removed_by_user": set()}
        self.assertTrue(has_customization)
        self.assertEqual(customization, self.package.get_user_customization(benefits))

    def test_no_user_customization_if_all_benefits_from_package(self):
        has_customization = self.package.has_user_customization(self.package_benefits)
        customization = {"added_by_user": set(), "removed_by_user": set()}
        self.assertFalse(has_customization)
        self.assertEqual(customization, self.package.get_user_customization(self.package_benefits))

    def test_has_user_customization_if_missing_package_benefit(self):
        removed_benefit = self.package_benefits.pop()
        has_customization = self.package.has_user_customization(self.package_benefits)
        customization = {"added_by_user": set(), "removed_by_user": {removed_benefit}}
        self.assertTrue(has_customization)
        self.assertEqual(customization, self.package.get_user_customization(self.package_benefits))

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

    def test_clone_package_to_next_year(self):
        pkg = baker.make(SponsorshipPackage, year=2022, advertise=True, logo_dimension=300)
        pkg_2023, created = pkg.clone(year=2023)
        self.assertTrue(created)
        self.assertTrue(pkg_2023.pk)
        self.assertEqual(2023, pkg_2023.year)
        self.assertEqual(pkg.name, pkg_2023.name)
        self.assertEqual(pkg.order, pkg_2023.order)
        self.assertEqual(pkg.sponsorship_amount, pkg_2023.sponsorship_amount)
        self.assertEqual(True, pkg_2023.advertise)
        self.assertEqual(300, pkg_2023.logo_dimension)
        self.assertEqual(pkg.slug, pkg_2023.slug)

    def test_clone_does_not_repeate_already_cloned_package(self):
        pkg_2023, created = self.package.clone(year=2023)
        repeated_pkg_2023, created = self.package.clone(year=2023)
        self.assertFalse(created)
        self.assertEqual(pkg_2023.pk, repeated_pkg_2023.pk)

    def test_get_default_revenue_split(self):
        benefits = baker.make(SponsorshipBenefit, internal_value=int(random.random() * 1000), _quantity=12)
        program_names = set((b.program.name for b in benefits))
        pkg1 = baker.make(SponsorshipPackage, year=2024, advertise=True, logo_dimension=300, benefits=benefits[:3])
        pkg2 = baker.make(SponsorshipPackage, year=2024, advertise=True, logo_dimension=300, benefits=benefits[3:7])
        pkg3 = baker.make(SponsorshipPackage, year=2024, advertise=True, logo_dimension=300, benefits=benefits[7:])
        splits = [pkg.get_default_revenue_split() for pkg in (pkg1, pkg2, pkg3)]
        split_names = set((name for split in splits for name, _ in split))
        totals = [sum((pct for _, pct in split)) for split in splits]
        # since the split percentages are rounded, they may not always total exactly 100.000
        self.assertAlmostEqual(totals[0], 100, delta=0.1)
        self.assertAlmostEqual(totals[1], 100, delta=0.1)
        self.assertAlmostEqual(totals[2], 100, delta=0.1)
        self.assertEqual(split_names, program_names)


class SponsorContactModelTests(TestCase):
    def test_get_primary_contact_for_sponsor(self):
        sponsor = baker.make(Sponsor)
        baker.make(SponsorContact, sponsor=sponsor, primary=False, _quantity=5)
        baker.make(SponsorContact, primary=True)  # from other sponsor

        self.assertEqual(5, SponsorContact.objects.filter(sponsor=sponsor).count())
        with self.assertRaises(SponsorContact.DoesNotExist):
            SponsorContact.objects.get_primary_contact(sponsor)
        self.assertIsNone(sponsor.primary_contact)

        primary_contact = baker.make(SponsorContact, primary=True, sponsor=sponsor)
        self.assertEqual(
            SponsorContact.objects.get_primary_contact(sponsor), primary_contact
        )
        self.assertEqual(sponsor.primary_contact, primary_contact)


class ContractModelTests(TestCase):
    def setUp(self):
        self.sponsorship = baker.make(Sponsorship, _fill_optional="sponsor")
        baker.make(
            SponsorshipBenefit,
            program__name="PSF",
            name=seq("benefit"),
            order=seq(1),
            _quantity=3,
        )
        self.sponsorship_benefits = SponsorshipBenefit.objects.all()

    def test_auto_increment_draft_revision_on_save(self):
        contract = baker.make_recipe("sponsors.tests.empty_contract")
        self.assertEqual(contract.status, Contract.DRAFT)
        self.assertEqual(contract.revision, 0)

        num_updates = 5
        for i in range(num_updates):
            contract.save()
            contract.refresh_from_db()

        self.assertEqual(contract.revision, num_updates)

    def test_does_not_auto_increment_draft_revision_on_save_if_other_states(self):
        contract = baker.make_recipe("sponsors.tests.empty_contract", revision=10)

        choices = Contract.STATUS_CHOICES
        other_status = [c[0] for c in choices if c[0] != Contract.DRAFT]
        for status in other_status:
            contract.status = status
            contract.save()
            contract.refresh_from_db()
            self.assertEqual(contract.status, status)
            self.assertEqual(contract.revision, 10)
            contract.save()  # perform extra save
            contract.refresh_from_db()
            self.assertEqual(contract.revision, 10)

    def test_create_new_contract_from_sponsorship_sets_sponsor_info_and_contact(
        self,
    ):
        contract = Contract.new(self.sponsorship)
        contract.refresh_from_db()

        sponsor = self.sponsorship.sponsor
        expected_info = f"{sponsor.name}, {sponsor.description}"

        self.assertEqual(contract.sponsorship, self.sponsorship)
        self.assertEqual(contract.sponsor_info, expected_info)
        self.assertEqual(contract.sponsor_contact, "")

    def test_create_new_contract_from_sponsorship_sets_sponsor_contact_and_primary(
        self,
    ):
        sponsor = self.sponsorship.sponsor
        contact = baker.make(
            SponsorContact, sponsor=self.sponsorship.sponsor, primary=True
        )

        contract = Contract.new(self.sponsorship)
        expected_contact = f"{contact.name} - {contact.phone} | {contact.email}"

        self.assertEqual(contract.sponsor_contact, expected_contact)

    def test_format_benefits_without_legal_clauses(self):
        for benefit in self.sponsorship_benefits:
            SponsorBenefit.new_copy(benefit, sponsorship=self.sponsorship)

        contract = Contract.new(self.sponsorship)

        self.assertEqual(contract.legal_clauses.raw, "")
        self.assertEqual(contract.legal_clauses.markup_type, "markdown")

        b1, b2, b3 = self.sponsorship.benefits.all()
        expected_benefits_list = f"""- PSF - {b1.name}
- PSF - {b2.name}
- PSF - {b3.name}"""

        self.assertEqual(contract.benefits_list.raw, expected_benefits_list)
        self.assertEqual(contract.benefits_list.markup_type, "markdown")

    def test_format_benefits_with_legal_clauses(self):
        baker.make(LegalClause, _quantity=len(self.sponsorship_benefits))
        legal_clauses = list(LegalClause.objects.all())

        for i, benefit in enumerate(self.sponsorship_benefits):
            clause = legal_clauses[i]
            benefit.legal_clauses.add(clause)
            SponsorBenefit.new_copy(benefit, sponsorship=self.sponsorship)
        self.sponsorship_benefits.first().legal_clauses.add(
            clause
        )  # first benefit with 2 legal clauses

        contract = Contract.new(self.sponsorship)

        c1, c2, c3 = legal_clauses
        expected_legal_clauses = f"""[^1]: {c1.clause}
[^2]: {c2.clause}
[^3]: {c3.clause}"""
        self.assertEqual(contract.legal_clauses.raw, expected_legal_clauses)
        self.assertEqual(contract.legal_clauses.markup_type, "markdown")

        b1, b2, b3 = self.sponsorship.benefits.all()
        expected_benefits_list = f"""- PSF - {b1.name} [^1][^3]
- PSF - {b2.name} [^2]
- PSF - {b3.name} [^3]"""

        self.assertEqual(contract.benefits_list.raw, expected_benefits_list)
        self.assertEqual(contract.benefits_list.markup_type, "markdown")

    def test_control_contract_next_status(self):
        SOW = Contract
        states_map = {
            SOW.DRAFT: [SOW.AWAITING_SIGNATURE, SOW.EXECUTED],
            SOW.OUTDATED: [],
            SOW.AWAITING_SIGNATURE: [SOW.EXECUTED, SOW.NULLIFIED],
            SOW.EXECUTED: [],
            SOW.NULLIFIED: [SOW.DRAFT],
        }
        for status, exepcted in states_map.items():
            contract = baker.prepare_recipe(
                "sponsors.tests.empty_contract",
                sponsorship__sponsor__name="foo",
                status=status,
            )
            self.assertEqual(contract.next_status, exepcted)

    def test_set_final_document_version(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", sponsorship__sponsor__name="foo"
        )
        content = b"pdf binary content"
        self.assertFalse(contract.document.name)

        contract.set_final_version(content)
        contract.refresh_from_db()

        self.assertTrue(contract.document.name)
        self.assertEqual(contract.status, Contract.AWAITING_SIGNATURE)

    def test_set_final_document_version_saves_docx_document_too(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", sponsorship__sponsor__name="foo"
        )
        content = b"pdf binary content"
        docx_content = b"pdf binary content"

        contract.set_final_version(content, docx_content)
        contract.refresh_from_db()

        self.assertTrue(contract.document_docx.name)
        self.assertEqual(contract.status, Contract.AWAITING_SIGNATURE)

    def test_raise_invalid_status_exception_if_not_draft(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE
        )

        with self.assertRaises(InvalidStatusException):
            contract.set_final_version(b"content")

    def test_execute_contract(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE
        )

        contract.execute()
        contract.refresh_from_db()

        self.assertEqual(contract.status, Contract.EXECUTED)
        self.assertEqual(contract.sponsorship.status, Sponsorship.FINALIZED)
        self.assertEqual(contract.sponsorship.finalized_on, date.today())

    def test_raise_invalid_status_when_trying_to_execute_contract_if_not_awaiting_signature(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", status=Contract.OUTDATED
        )

        with self.assertRaises(InvalidStatusException):
            contract.execute()

    def test_nullify_contract(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE
        )

        contract.nullify()
        contract.refresh_from_db()

        self.assertEqual(contract.status, Contract.NULLIFIED)

    def test_raise_invalid_status_when_trying_to_nullify_contract_if_not_awaiting_signature(self):
        contract = baker.make_recipe(
            "sponsors.tests.empty_contract", status=Contract.DRAFT
        )

        with self.assertRaises(InvalidStatusException):
            contract.nullify()


class SponsorBenefitModelTests(TestCase):

    def setUp(self):
        self.sponsorship = baker.make(Sponsorship)
        self.sponsorship_benefit = baker.make(SponsorshipBenefit, name='Benefit')

    def test_new_copy_also_add_benefit_feature_when_creating_sponsor_benefit(self):
        benefit_config = baker.make(LogoPlacementConfiguration, benefit=self.sponsorship_benefit)
        self.assertEqual(0, LogoPlacement.objects.count())

        sponsor_benefit = SponsorBenefit.new_copy(
            self.sponsorship_benefit, sponsorship=self.sponsorship
        )

        self.assertEqual(1, LogoPlacement.objects.count())
        benefit_feature = sponsor_benefit.features.get()
        self.assertIsInstance(benefit_feature, LogoPlacement)
        self.assertEqual(benefit_feature.publisher, benefit_config.publisher)
        self.assertEqual(benefit_feature.logo_place, benefit_config.logo_place)

    def test_new_copy_do_not_save_unexisting_features(self):
        benefit_config = baker.make(
            TieredBenefitConfiguration,
            package__name='Another package',
            benefit=self.sponsorship_benefit,
        )
        self.assertEqual(0, TieredBenefit.objects.count())

        sponsor_benefit = SponsorBenefit.new_copy(
            self.sponsorship_benefit, sponsorship=self.sponsorship
        )

        self.assertEqual(0, TieredBenefit.objects.count())
        self.assertFalse(sponsor_benefit.features.exists())

    def test_sponsor_benefit_name_for_display(self):
        name = "Benefit"
        sponsor_benefit = baker.make(SponsorBenefit, name=name)
        # benefit name if no features
        self.assertEqual(sponsor_benefit.name_for_display, name)
        # apply display modifier from features
        benefit_config = baker.make(
            TieredBenefit,
            sponsor_benefit=sponsor_benefit,
            quantity=10
        )
        self.assertEqual(sponsor_benefit.name_for_display, f"{name} (10)")

    def test_sponsor_benefit_from_standalone_one(self):
        self.sponsorship_benefit.standalone = True
        self.sponsorship_benefit.save()
        sponsor_benefit = SponsorBenefit.new_copy(
            self.sponsorship_benefit, sponsorship=self.sponsorship
        )

        self.assertTrue(sponsor_benefit.added_by_user)
        self.assertTrue(sponsor_benefit.standalone)

    def test_reset_attributes_updates_all_basic_information(self):
        benefit = baker.make(
            SponsorBenefit, sponsorship_benefit=self.sponsorship_benefit
        )
        # both have different random values
        self.assertNotEqual(benefit.name, self.sponsorship_benefit.name)

        benefit.reset_attributes(self.sponsorship_benefit)
        benefit.refresh_from_db()

        self.assertEqual(benefit.name, self.sponsorship_benefit.name)
        self.assertEqual(benefit.description, self.sponsorship_benefit.description)
        self.assertEqual(benefit.program_name, self.sponsorship_benefit.program.name)
        self.assertEqual(benefit.program, self.sponsorship_benefit.program)
        self.assertEqual(benefit.benefit_internal_value, self.sponsorship_benefit.internal_value)
        self.assertEqual(benefit.standalone, self.sponsorship_benefit.standalone)

    def test_reset_attributes_add_new_features(self):
        RequiredTextAssetConfiguration.objects.create(
            benefit=self.sponsorship_benefit,
            related_to="sponsorship",
            internal_name="foo",
            label="Text",
        )
        benefit = baker.make(
            SponsorBenefit, sponsorship_benefit=self.sponsorship_benefit
        )
        # no previous feature
        self.assertFalse(benefit.features.count())

        benefit.reset_attributes(self.sponsorship_benefit)
        benefit.refresh_from_db()

        self.assertEqual(1, benefit.features.count())

    def test_reset_attributes_delete_removed_features(self):
        cfg = RequiredTextAssetConfiguration.objects.create(
            benefit=self.sponsorship_benefit,
            related_to="sponsorship",
            internal_name="foo",
            label="Text",
        )
        benefit = SponsorBenefit.new_copy(
            self.sponsorship_benefit, sponsorship=self.sponsorship
        )
        self.assertEqual(1, benefit.features.count())
        cfg.delete()

        benefit.reset_attributes(self.sponsorship_benefit)
        benefit.refresh_from_db()

        # no previous feature
        self.assertFalse(benefit.features.count())

    def test_reset_attributes_recreate_features_but_keeping_previous_values(self):
        cfg = RequiredTextAssetConfiguration.objects.create(
            benefit=self.sponsorship_benefit,
            related_to="sponsorship",
            internal_name="foo",
            label="Text",
        )
        benefit = SponsorBenefit.new_copy(
            self.sponsorship_benefit, sponsorship=self.sponsorship
        )

        feature = RequiredTextAsset.objects.get()
        feature.value = "foo"
        feature.save()
        cfg.label = "New text"
        cfg.save()

        benefit.reset_attributes(self.sponsorship_benefit)
        benefit.refresh_from_db()

        # no previous feature
        self.assertEqual(1, benefit.features.count())
        asset = benefit.features.required_assets().get()
        self.assertEqual(asset.label, "New text")
        self.assertEqual(asset.value, "foo")

    def test_clone_benefit_regular_attributes_to_a_new_year(self):
        benefit = baker.make(
            SponsorshipBenefit,
            name='Benefit',
            description="desc",
            program__name="prog",
            package_only=False,
            new=True,
            unavailable=True,
            standalone=True,
            internal_description="internal desc",
            internal_value=300,
            capacity=100,
            soft_capacity=True,
            year=2022
        )
        benefit_2023, created = benefit.clone(year=2023)
        self.assertTrue(created)
        self.assertEqual("Benefit", benefit_2023.name)
        self.assertEqual("desc", benefit_2023.description)
        self.assertEqual(benefit.program, benefit_2023.program)
        self.assertFalse(benefit_2023.package_only)
        self.assertTrue(benefit_2023.new)
        self.assertTrue(benefit_2023.unavailable)
        self.assertTrue(benefit_2023.standalone)
        self.assertEqual("internal desc", benefit_2023.internal_description)
        self.assertEqual(300, benefit_2023.internal_value)
        self.assertEqual(100, benefit_2023.capacity)
        self.assertTrue(benefit_2023.soft_capacity)
        self.assertEqual(2023, benefit_2023.year)
        self.assertEqual(benefit.order, benefit_2023.order)

    def test_clone_benefit_should_be_idempotent(self):
        benefit_2023, created = self.sponsorship_benefit.clone(year=2023)
        repeated, created = self.sponsorship_benefit.clone(year=2023)
        self.assertFalse(created)
        self.assertEqual(benefit_2023.pk, repeated.pk)

    def test_clone_related_objects_as_well(self):
        pkgs = baker.make(SponsorshipPackage, _quantity=2)
        clauses = baker.make(LegalClause, _quantity=2)
        self.sponsorship_benefit.legal_clauses.add(*clauses)
        self.sponsorship_benefit.packages.add(*pkgs)

        benefit_2023, _ = self.sponsorship_benefit.clone(2023)
        benefit_2023.refresh_from_db()

        self.assertEqual(4, SponsorshipPackage.objects.count())
        self.assertEqual(2023, benefit_2023.packages.values_list("year", flat=True).distinct().first())
        self.assertEqual(4, LegalClause.objects.count())
        self.assertEqual(2, benefit_2023.legal_clauses.count())

    def test_clone_benefit_feature_configurations(self):
        cfg_1 = baker.make(
            LogoPlacementConfiguration,
            publisher = PublisherChoices.FOUNDATION,
            logo_place = LogoPlacementChoices.FOOTER,
            benefit=self.sponsorship_benefit
        )
        cfg_2 = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSOR.value,
            internal_name="config_name",
            benefit=self.sponsorship_benefit
        )

        benefit_2023, _ = self.sponsorship_benefit.clone(2023)

        self.assertEqual(2, LogoPlacementConfiguration.objects.count())
        self.assertEqual(2, RequiredTextAssetConfiguration.objects.count())
        self.assertEqual(1, RequiredTextAssetConfiguration.objects.filter(benefit=benefit_2023).count())
        self.assertEqual(1, RequiredTextAssetConfiguration.objects.filter(benefit=benefit_2023).count())


class LegalClauseTests(TestCase):

    def test_clone_legal_clause(self):
        clause = baker.make(LegalClause)
        new_clause = clause.clone()
        self.assertEqual(clause.internal_name, new_clause.internal_name)
        self.assertEqual(clause.clause, new_clause.clause)
        self.assertEqual(clause.notes, new_clause.notes)
        self.assertEqual(clause.order, new_clause.order)


###########
# Email notification tests
class SponsorEmailNotificationTemplateTests(TestCase):

    def setUp(self):
        self.notification = baker.make(
            'sponsors.SponsorEmailNotificationTemplate',
            subject="Subject - {{ sponsor_name }}",
            content="Hi {{ sponsor_name }}, how are you?",
        )
        self.sponsorship = baker.make(Sponsorship, sponsor__name="Foo")
        self.contact = baker.make(
            SponsorContact, sponsor=self.sponsorship.sponsor, primary=True
        )

    def test_map_sponsorship_info_to_simplified_context_data(self):
        expected_context = {
            "sponsor_name": "Foo",
            "sponsorship_start_date": self.sponsorship.start_date,
            "sponsorship_end_date": self.sponsorship.end_date,
            "sponsorship_status": self.sponsorship.status,
            "sponsorship_level": self.sponsorship.level_name,
            "extra": "foo"
        }
        context = self.notification.get_email_context_data(sponsorship=self.sponsorship, extra="foo")
        self.assertEqual(expected_context, context)

    def test_get_email_message(self):
        manager = baker.make(
            SponsorContact, sponsor=self.sponsorship.sponsor, manager=True
        )
        baker.make(SponsorContact, sponsor=self.sponsorship.sponsor, accounting=True)

        email = self.notification.get_email_message(
            self.sponsorship, to_primary=True, to_manager=True
        )

        self.assertIsInstance(email, EmailMessage)
        self.assertEqual("Subject - Foo", email.subject)
        self.assertEqual("Hi Foo, how are you?", email.body)
        self.assertEqual(settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL, email.from_email)
        self.assertEqual(2, len(email.to))
        self.assertIn(self.contact.email, email.to)
        self.assertIn(manager.email, email.to)
        self.assertEqual(email.cc, [])
        self.assertEqual(email.bcc, [])
        self.assertEqual(email.attachments, [])

    def test_get_email_message_returns_none_if_no_contact(self):
        self.contact.delete()
        SponsorContact.objects.all().delete()
        email = self.notification.get_email_message(self.sponsorship, to_primary=True, to_manager=True)
        self.assertIsNone(email)


###########
####### Benefit features/configuration tests
###########
class LogoPlacementConfigurationModelTests(TestCase):

    def setUp(self):
        self.config = baker.make(
            LogoPlacementConfiguration,
            publisher=PublisherChoices.FOUNDATION,
            logo_place=LogoPlacementChoices.FOOTER,
        )

    def test_get_benefit_feature_respecting_configuration(self):
        benefit_feature = self.config.get_benefit_feature()

        self.assertIsInstance(benefit_feature, LogoPlacement)
        self.assertEqual(benefit_feature.publisher, PublisherChoices.FOUNDATION)
        self.assertEqual(benefit_feature.logo_place, LogoPlacementChoices.FOOTER)
        # can't save object without related sponsor benefit
        self.assertIsNone(benefit_feature.pk)
        self.assertIsNone(benefit_feature.sponsor_benefit_id)

    def test_display_modifier_returns_same_name(self):
        name = 'Benefit'
        self.assertEqual(name, self.config.display_modifier(name))

    def test_clone_configuration_for_new_sponsorship_benefit(self):
        sp_benefit = baker.make(SponsorshipBenefit)

        new_cfg, created = self.config.clone(sp_benefit)

        self.assertTrue(created)
        self.assertEqual(2, LogoPlacementConfiguration.objects.count())
        self.assertEqual(PublisherChoices.FOUNDATION, new_cfg.publisher)
        self.assertEqual(LogoPlacementChoices.FOOTER, new_cfg.logo_place)
        self.assertEqual(sp_benefit, new_cfg.benefit)

        repeated, created = self.config.clone(sp_benefit)
        self.assertFalse(created)
        self.assertEqual(new_cfg.pk, repeated.pk)


class TieredBenefitConfigurationModelTests(TestCase):

    def setUp(self):
        self.package = baker.make(SponsorshipPackage, year=2022)
        self.config = baker.make(
            TieredBenefitConfiguration,
            package=self.package,
            display_label="Foo",
            quantity=10,
        )

    def test_get_benefit_feature_respecting_configuration(self):
        sponsor_benefit = baker.make(SponsorBenefit, sponsorship__package=self.package)

        benefit_feature = self.config.get_benefit_feature(sponsor_benefit=sponsor_benefit)

        self.assertIsInstance(benefit_feature, TieredBenefit)
        self.assertEqual(benefit_feature.package, self.package)
        self.assertEqual(benefit_feature.quantity, self.config.quantity)
        self.assertEqual(benefit_feature.display_label, "Foo")

    def test_do_not_return_feature_if_benefit_from_other_package(self):
        sponsor_benefit = baker.make(SponsorBenefit, sponsorship__package__name='Other')

        benefit_feature = self.config.get_benefit_feature(sponsor_benefit=sponsor_benefit)

        self.assertIsNone(benefit_feature)

    def test_display_modifier_only_modifies_name_if_same_package(self):
        name = "Benefit"
        other_package = baker.make(SponsorshipPackage)

        # modifies for the same package as the config + label prioritized
        self.config.save(update_fields=["display_label"])
        modified_name = self.config.display_modifier(name, package=self.package)
        self.assertEqual(modified_name, f"{name} (Foo)")

        # modifies for the same package as the config
        self.config.display_label = ""
        self.config.save(update_fields=["display_label"])
        modified_name = self.config.display_modifier(name, package=self.package)
        self.assertEqual(modified_name, f"{name} (10)")

        # for a package different from the config's one
        modified_name = self.config.display_modifier(name, package=other_package)
        self.assertEqual(modified_name, name)

    def test_clone_tiered_quantity_configuration(self):
        benefit = baker.make(SponsorshipBenefit, year=2023)

        new_cfg, created = self.config.clone(benefit)

        self.assertTrue(created)
        self.assertEqual(2, TieredBenefitConfiguration.objects.count())
        self.assertEqual(self.config.quantity, new_cfg.quantity)
        self.assertEqual("Foo", new_cfg.display_label)
        self.assertNotEqual(self.package, new_cfg.package)
        self.assertEqual(self.package.slug, new_cfg.package.slug)
        self.assertEqual(2023, new_cfg.package.year)
        self.assertEqual(benefit, new_cfg.benefit)

        repeated, created = self.config.clone(benefit)
        self.assertFalse(created)
        self.assertEqual(new_cfg.pk, repeated.pk)


class LogoPlacementTests(TestCase):

    def test_display_modifier_does_not_change_the_name(self):
        placement = baker.make(LogoPlacement)
        name = 'Benefit'
        self.assertEqual(placement.display_modifier(name), name)


class TieredBenefitTests(TestCase):

    def test_display_modifier_adds_quantity_to_the_name(self):
        placement = baker.make(TieredBenefit, quantity=10)
        name = 'Benefit'
        self.assertEqual(placement.display_modifier(name), 'Benefit (10)')

    def test_display_modifier_adds_display_label_to_the_name(self):
        placement = baker.make(TieredBenefit, quantity=10, display_label="Foo")
        name = 'Benefit'
        self.assertEqual(placement.display_modifier(name), 'Benefit (Foo)')


class RequiredImgAssetConfigurationTests(TestCase):

    def setUp(self):
        self.sponsor_benefit = baker.make(SponsorBenefit, sponsorship__sponsor__name='Foo')
        self.config = baker.make(
            RequiredImgAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSOR.value,
            internal_name="config_name",
        )

    def test_get_benefit_feature_respecting_configuration(self):
        benefit_feature = self.config.get_benefit_feature(sponsor_benefit=self.sponsor_benefit)

        self.assertIsInstance(benefit_feature, RequiredImgAsset)
        self.assertEqual(benefit_feature.max_width, self.config.max_width)
        self.assertEqual(benefit_feature.min_width, self.config.min_width)
        self.assertEqual(benefit_feature.max_height, self.config.max_height)
        self.assertEqual(benefit_feature.min_height, self.config.min_height)

    def test_create_benefit_feature_and_sponsor_generic_img_assets(self):
        sponsor = self.sponsor_benefit.sponsorship.sponsor

        feature = self.config.create_benefit_feature(self.sponsor_benefit)
        asset = ImgAsset.objects.get()

        self.assertIsInstance(feature, RequiredImgAsset)
        self.assertTrue(feature.pk)
        self.assertEqual(self.config.internal_name, asset.internal_name)
        self.assertEqual(sponsor, asset.content_object)
        self.assertFalse(asset.image.name)

    def test_clone_configuration_for_new_sponsorship_benefit_without_due_date(self):
        sp_benefit = baker.make(SponsorshipBenefit, year=2023)

        new_cfg, created = self.config.clone(sp_benefit)

        self.assertTrue(created)
        self.assertEqual(2, RequiredImgAssetConfiguration.objects.count())
        self.assertEqual(new_cfg.internal_name, f"{self.config.internal_name}_2023")
        self.assertEqual(new_cfg.max_width, self.config.max_width)
        self.assertEqual(new_cfg.min_width, self.config.min_width)
        self.assertEqual(new_cfg.max_height, self.config.max_height)
        self.assertEqual(new_cfg.min_height, self.config.min_height)
        self.assertEqual(new_cfg.due_date, new_cfg.due_date)
        self.assertEqual(sp_benefit, new_cfg.benefit)

        repeated, created = self.config.clone(sp_benefit)
        self.assertFalse(created)
        self.assertEqual(new_cfg.pk, repeated.pk)


class RequiredTextAssetConfigurationTests(TestCase):

    def setUp(self):
        self.sponsor_benefit = baker.make(SponsorBenefit, sponsorship__sponsor__name='Foo')
        self.config = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSOR.value,
            internal_name="config_name",
            _fill_optional=True,
        )

    def test_get_benefit_feature_respecting_configuration(self):
        benefit_feature = self.config.get_benefit_feature(sponsor_benefit=self.sponsor_benefit)

        self.assertIsInstance(benefit_feature, RequiredTextAsset)
        self.assertEqual(benefit_feature.label, self.config.label)
        self.assertEqual(benefit_feature.help_text, self.config.help_text)

    def test_create_benefit_feature_and_sponsor_generic_text_asset(self):
        sponsor = self.sponsor_benefit.sponsorship.sponsor

        feature = self.config.create_benefit_feature(self.sponsor_benefit)
        asset = TextAsset.objects.get()

        self.assertIsInstance(feature, RequiredTextAsset)
        self.assertTrue(feature.pk)
        self.assertEqual(self.config.internal_name, asset.internal_name)
        self.assertEqual(sponsor, asset.content_object)
        self.assertFalse(asset.text)

    def test_relate_asset_with_sponsorship_respecting_config(self):
        self.config.related_to = AssetsRelatedTo.SPONSORSHIP.value
        self.config.save()
        sponsorship = self.sponsor_benefit.sponsorship

        self.config.create_benefit_feature(self.sponsor_benefit)

        asset = TextAsset.objects.get()
        self.assertEqual(sponsorship, asset.content_object)

    def test_cant_create_same_asset_twice(self):
        self.config.create_benefit_feature(self.sponsor_benefit)
        self.sponsor_benefit.refresh_from_db()
        self.config.create_benefit_feature(self.sponsor_benefit)
        self.assertEqual(1, TextAsset.objects.count())

    def test_clone_configuration_for_new_sponsorship_benefit_with_new_due_date(self):
        sp_benefit = baker.make(SponsorshipBenefit, year=2023)

        self.config.due_date = timezone.now().replace(year=2022)
        self.config.save()
        new_cfg, created = self.config.clone(sp_benefit)

        self.assertTrue(created)
        self.assertEqual(2, RequiredTextAssetConfiguration.objects.count())
        self.assertEqual(new_cfg.internal_name, f"{self.config.internal_name}_2023")
        self.assertEqual(new_cfg.label, self.config.label)
        self.assertEqual(new_cfg.help_text, self.config.help_text)
        self.assertEqual(new_cfg.max_length, self.config.max_length)
        self.assertEqual(new_cfg.due_date.day, self.config.due_date.day)
        self.assertEqual(new_cfg.due_date.month, self.config.due_date.month)
        self.assertEqual(new_cfg.due_date.year, 2023)
        self.assertEqual(sp_benefit, new_cfg.benefit)

        repeated, created = self.config.clone(sp_benefit)
        self.assertFalse(created)
        self.assertEqual(new_cfg.pk, repeated.pk)


class RequiredTextAssetTests(TestCase):

    def setUp(self):
        self.sponsor_benefit = baker.make(SponsorBenefit, sponsorship__sponsor__name='Foo')

    def test_get_value_from_sponsor_asset(self):
        config = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSOR.value,
            _fill_optional=True,
        )
        text_asset_feature = config.create_benefit_feature(self.sponsor_benefit)
        asset = TextAsset.objects.get()

        self.assertEqual("", text_asset_feature.value)
        asset.text = "sponsor information"
        asset.save()

        self.assertEqual("sponsor information", text_asset_feature.value)

    def test_get_value_from_sponsorship_asset(self):
        config = baker.make(
            RequiredTextAssetConfiguration,
            related_to=AssetsRelatedTo.SPONSORSHIP.value,
            _fill_optional=True,
        )
        text_asset_feature = config.create_benefit_feature(self.sponsor_benefit)
        asset = TextAsset.objects.get()

        self.assertEqual("", text_asset_feature.value)
        asset.text = "sponsorship information"
        asset.save()

        self.assertEqual("sponsorship information", text_asset_feature.value)

    def test_required_asset_class_inherits_from_expected_classed(self):
        classes = (RequiredAssetMixin, BaseRequiredTextAsset, BenefitFeature)
        issubclass(RequiredTextAsset, classes)

    def test_build_form_field_from_input(self):
        text_asset = baker.make(RequiredTextAsset, _fill_optional=True)
        field = text_asset.as_form_field()
        self.assertIsInstance(field, forms.CharField)
        self.assertIsInstance(field.widget, forms.Textarea)
        self.assertFalse(field.required)
        self.assertEqual(text_asset.help_text, field.help_text)
        self.assertEqual(text_asset.label, field.label)

    def test_build_form_field_from_input_with_max_length(self):
        text_asset = baker.make(RequiredTextAsset, _fill_optional=True, max_length=256)
        field = text_asset.as_form_field()
        self.assertIsInstance(field, forms.CharField)
        self.assertIsInstance(field.widget, forms.TextInput)
        self.assertFalse(field.required)
        self.assertEqual(text_asset.help_text, field.help_text)
        self.assertEqual(text_asset.label, field.label)


class RequiredImgAssetTests(TestCase):
    def test_required_asset_class_inherits_from_expected_classed(self):
        classes = (RequiredAssetMixin, BaseRequiredImgAsset, BenefitFeature)
        issubclass(RequiredImgAsset, classes)

    def test_build_form_field_from_input(self):
        text_asset = baker.make(RequiredImgAsset, _fill_optional=True)
        field = text_asset.as_form_field()
        self.assertIsInstance(field, forms.ImageField)
        self.assertFalse(field.required)
        self.assertEqual(text_asset.help_text, field.help_text)
        self.assertEqual(text_asset.label, field.label)
        self.assertIsInstance(field.widget, forms.ClearableFileInput)


class EmailTargetableConfigurationTest(TestCase):

    def test_clone_configuration_for_new_sponsorship_benefit_with_new_due_date(self):
        config = baker.make(EmailTargetableConfiguration)
        benefit = baker.make(SponsorshipBenefit, year=2023)

        new_cfg, created = config.clone(benefit)

        self.assertTrue(created)
        self.assertEqual(2, EmailTargetableConfiguration.objects.count())
        self.assertEqual(benefit, new_cfg.benefit)

        repeated, created = config.clone(benefit)
        self.assertFalse(created)
        self.assertEqual(new_cfg.pk, repeated.pk)
