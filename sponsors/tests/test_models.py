from datetime import date, timedelta
from model_bakery import baker, seq

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from ..models import (
    Contract,
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
    TieredQuantity,
    TieredQuantityConfiguration
)
from ..exceptions import (
    SponsorWithExistingApplicationException,
    SponsorshipInvalidDateRangeException,
    InvalidStatusException,
)
from ..enums import PublisherChoices, LogoPlacementChoices


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
            TieredQuantityConfiguration,
            package__name='Package',
            benefit=benefit,
        )

        self.assertEqual(benefit.name_for_display(), self.sponsorship_benefit.name)
        self.assertFalse(benefit.has_tiers)

    def test_name_for_display_without_specifying_package(self):
        benefit = baker.make(SponsorshipBenefit, name='Benefit')
        benefit_config = baker.make(
            TieredQuantityConfiguration,
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
        self.assertEqual(sponsorship.agreed_fee, 100)  # can display the price because there's not customizations
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
        expected_info = f"{sponsor.name} with address {sponsor.full_address} and contact {sponsor.primary_phone}"

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
            SOW.DRAFT: [SOW.AWAITING_SIGNATURE],
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
            "sponsors.tests.empty_contract", status=Contract.DRAFT
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
            TieredQuantityConfiguration,
            package__name='Another package',
            benefit=self.sponsorship_benefit,
        )
        self.assertEqual(0, TieredQuantity.objects.count())

        sponsor_benefit = SponsorBenefit.new_copy(
            self.sponsorship_benefit, sponsorship=self.sponsorship
        )

        self.assertEqual(0, TieredQuantity.objects.count())
        self.assertFalse(sponsor_benefit.features.exists())

    def test_sponsor_benefit_name_for_display(self):
        name = "Benefit"
        sponsor_benefit = baker.make(SponsorBenefit, name=name)
        # benefit name if no features
        self.assertEqual(sponsor_benefit.name_for_display, name)
        # apply display modifier from features
        benefit_config = baker.make(
            TieredQuantity,
            sponsor_benefit=sponsor_benefit,
            quantity=10
        )
        self.assertEqual(sponsor_benefit.name_for_display, f"{name} (10)")

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


class TieredQuantityConfigurationModelTests(TestCase):

    def setUp(self):
        self.package = baker.make(SponsorshipPackage)
        self.config = baker.make(
            TieredQuantityConfiguration,
            package=self.package,
            quantity=10,
        )

    def test_get_benefit_feature_respecting_configuration(self):
        sponsor_benefit = baker.make(SponsorBenefit, sponsorship__level_name=self.package.name)

        benefit_feature = self.config.get_benefit_feature(sponsor_benefit=sponsor_benefit)

        self.assertIsInstance(benefit_feature, TieredQuantity)
        self.assertEqual(benefit_feature.package, self.package)
        self.assertEqual(benefit_feature.quantity, self.config.quantity)

    def test_do_not_return_feature_if_benefit_from_other_package(self):
        sponsor_benefit = baker.make(SponsorBenefit, sponsorship__level_name='Other')

        benefit_feature = self.config.get_benefit_feature(sponsor_benefit=sponsor_benefit)

        self.assertIsNone(benefit_feature)

    def test_display_modifier_only_modifies_name_if_same_package(self):
        name = "Benefit"
        other_package = baker.make(SponsorshipPackage)

        # modifies for the same package as the config
        modified_name = self.config.display_modifier(name, package=self.package)
        self.assertEqual(modified_name, f"{name} (10)")

        # for a package different from the config's one
        modified_name = self.config.display_modifier(name, package=other_package)
        self.assertEqual(modified_name, name)


class LogoPlacementTests(TestCase):

    def test_display_modifier_does_not_change_the_name(self):
        placement = baker.make(LogoPlacement)
        name = 'Benefit'
        self.assertEqual(placement.display_modifier(name), name)


class TieredQuantityTests(TestCase):

    def test_display_modifier_adds_quantity_to_the_name(self):
        placement = baker.make(TieredQuantity, quantity=10)
        name = 'Benefit'
        self.assertEqual(placement.display_modifier(name), 'Benefit (10)')
