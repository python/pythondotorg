from unittest.mock import Mock
from model_bakery import baker
from datetime import timedelta, date

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from sponsors import use_cases
from sponsors.notifications import *
from sponsors.models import Sponsorship, Contract


class CreateSponsorshipApplicationUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock(), Mock()]
        self.use_case = use_cases.CreateSponsorshipApplicationUseCase(
            self.notifications
        )
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.sponsor = baker.make("sponsors.Sponsor")
        self.benefits = baker.make("sponsors.SponsorshipBenefit", _quantity=5)
        self.package = baker.make("sponsors.SponsorshipPackage")

    def test_create_new_sponsorship_using_benefits_and_package(self):
        sponsorship = self.use_case.execute(
            self.user, self.sponsor, self.benefits, self.package
        )

        self.assertTrue(sponsorship.pk)
        self.assertEqual(len(self.benefits), sponsorship.benefits.count())
        self.assertTrue(sponsorship.level_name)

    def test_send_notifications_using_sponsorship(self):
        sponsorship = self.use_case.execute(
            self.user, self.sponsor, self.benefits, self.package
        )

        for n in self.notifications:
            n.notify.assert_called_once_with(request=None, sponsorship=sponsorship)

    def test_build_use_case_with_correct_notifications(self):
        uc = use_cases.CreateSponsorshipApplicationUseCase.build()

        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(uc.notifications[0], AppliedSponsorshipNotificationToPSF)
        self.assertIsInstance(
            uc.notifications[1], AppliedSponsorshipNotificationToSponsors
        )


class RejectSponsorshipApplicationUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock(), Mock()]
        self.use_case = use_cases.RejectSponsorshipApplicationUseCase(
            self.notifications
        )
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.sponsorship = baker.make(Sponsorship)

    def test_update_sponsorship_as_rejected(self):
        self.use_case.execute(self.sponsorship)
        self.sponsorship.refresh_from_db()

        today = timezone.now().date()
        self.assertEqual(self.sponsorship.rejected_on, today)
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)

    def test_send_notifications_using_sponsorship(self):
        self.use_case.execute(self.sponsorship)

        for n in self.notifications:
            n.notify.assert_called_once_with(request=None, sponsorship=self.sponsorship)

    def test_build_use_case_with_correct_notifications(self):
        uc = use_cases.RejectSponsorshipApplicationUseCase.build()

        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(uc.notifications[0], RejectedSponsorshipNotificationToPSF)
        self.assertIsInstance(
            uc.notifications[1], RejectedSponsorshipNotificationToSponsors
        )


class ApproveSponsorshipApplicationUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock(), Mock()]
        self.use_case = use_cases.ApproveSponsorshipApplicationUseCase(
            self.notifications
        )
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.sponsorship = baker.make(Sponsorship, _fill_optional="sponsor")

        today = date.today()
        self.data = {
            "sponsorship_fee": 100,
            "level_name": "level",
            "start_date": today,
            "end_date": today + timedelta(days=10),
        }

    def test_update_sponsorship_as_approved_and_create_contract(self):
        self.use_case.execute(self.sponsorship, **self.data)
        self.sponsorship.refresh_from_db()

        today = timezone.now().date()
        self.assertEqual(self.sponsorship.approved_on, today)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        self.assertTrue(self.sponsorship.contract.pk)
        self.assertTrue(self.sponsorship.start_date)
        self.assertTrue(self.sponsorship.end_date)
        self.assertEqual(self.sponsorship.sponsorship_fee, 100)
        self.assertEqual(self.sponsorship.level_name, "level")

    def test_send_notifications_using_sponsorship(self):
        self.use_case.execute(self.sponsorship, **self.data)

        for n in self.notifications:
            n.notify.assert_called_once_with(
                request=None,
                sponsorship=self.sponsorship,
                contract=self.sponsorship.contract,
            )

    def test_build_use_case_without_notificationss(self):
        uc = use_cases.ApproveSponsorshipApplicationUseCase.build()
        self.assertEqual(len(uc.notifications), 1)
        self.assertIsInstance(uc.notifications[0], SponsorshipApprovalLogger)


class SendContractUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock(), Mock()]
        self.use_case = use_cases.SendContractUseCase(self.notifications)
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract")

    def test_send_and_update_contract_with_document(self):
        self.use_case.execute(self.contract)
        self.contract.refresh_from_db()

        self.assertTrue(self.contract.document.name)
        self.assertTrue(self.contract.awaiting_signature)
        for n in self.notifications:
            n.notify.assert_called_once_with(
                request=None,
                contract=self.contract,
            )

    def test_build_use_case_without_notificationss(self):
        uc = use_cases.SendContractUseCase.build()
        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(uc.notifications[0], ContractNotificationToPSF)
        self.assertIsInstance(
            uc.notifications[1], SentContractLogger
        )


class ExecuteContractUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock()]
        self.use_case = use_cases.ExecuteContractUseCase(self.notifications)
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE)

    def test_execute_and_update_database_object(self):
        self.use_case.execute(self.contract)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.EXECUTED)

    def test_build_use_case_without_notificationss(self):
        uc = use_cases.ExecuteContractUseCase.build()
        self.assertEqual(len(uc.notifications), 1)
        self.assertIsInstance(
            uc.notifications[0], ExecutedContractLogger
        )


class NullifyContractUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock()]
        self.use_case = use_cases.NullifyContractUseCase(self.notifications)
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE)

    def test_nullify_and_update_database_object(self):
        self.use_case.execute(self.contract)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.NULLIFIED)

    def test_build_use_case_without_notificationss(self):
        uc = use_cases.NullifyContractUseCase.build()
        self.assertEqual(len(uc.notifications), 1)
        self.assertIsInstance(
            uc.notifications[0], NullifiedContractLogger
        )
