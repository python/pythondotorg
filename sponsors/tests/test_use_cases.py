import os
from unittest.mock import Mock, patch, call
from model_bakery import baker
from datetime import timedelta, date
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.core.mail import EmailMessage
from django.core.files.uploadedfile import SimpleUploadedFile

from sponsors import use_cases
from sponsors.notifications import *
from sponsors.models import Sponsorship, Contract, SponsorEmailNotificationTemplate, Sponsor, SponsorshipBenefit, \
    SponsorshipPackage


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
        self.package = baker.make("sponsors.SponsorshipPackage")

        today = date.today()
        self.data = {
            "sponsorship_fee": 100,
            "package": self.package,
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
        self.assertEqual(self.sponsorship.package, self.package)
        self.assertEqual(self.sponsorship.level_name, self.package.name)
        self.assertFalse(self.sponsorship.renewal)


    def test_update_renewal_sponsorship_as_approved_and_create_contract(self):
        self.data.update({"renewal": True})
        self.use_case.execute(self.sponsorship, **self.data)
        self.sponsorship.refresh_from_db()

        today = timezone.now().date()
        self.assertEqual(self.sponsorship.approved_on, today)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        self.assertTrue(self.sponsorship.contract.pk)
        self.assertTrue(self.sponsorship.start_date)
        self.assertTrue(self.sponsorship.end_date)
        self.assertEqual(self.sponsorship.sponsorship_fee, 100)
        self.assertEqual(self.sponsorship.package, self.package)
        self.assertEqual(self.sponsorship.level_name, self.package.name)
        self.assertEqual(self.sponsorship.renewal, True)

    def test_send_notifications_using_sponsorship(self):
        self.use_case.execute(self.sponsorship, **self.data)

        for n in self.notifications:
            n.notify.assert_called_once_with(
                request=None,
                sponsorship=self.sponsorship,
                contract=self.sponsorship.contract,
            )

    def test_build_use_case_with_default_notificationss(self):
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
        self.assertTrue(self.contract.document_docx.name)
        self.assertTrue(self.contract.awaiting_signature)
        for n in self.notifications:
            n.notify.assert_called_once_with(
                request=None,
                contract=self.contract,
            )

    def test_build_use_case_with_default_notificationss(self):
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
        self.file = SimpleUploadedFile("contract.txt", b"Contract content")
        self.contract = baker.make_recipe(
            "sponsors.tests.empty_contract",
            status=Contract.AWAITING_SIGNATURE,
        )

    def tearDown(self):
        self.contract.refresh_from_db()
        if self.contract.signed_document:
            self.contract.signed_document.delete()

    def test_execute_and_update_database_object(self):
        self.use_case.execute(self.contract, self.file)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.EXECUTED)
        self.assertTrue(self.contract.signed_document.url)

    def test_build_use_case_with_default_notificationss(self):
        uc = use_cases.ExecuteContractUseCase.build()
        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(
            uc.notifications[0], ExecutedContractLogger
        )
        self.assertIsInstance(
            uc.notifications[1], RefreshSponsorshipsCache,
        )


class ExecuteExistingContractUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock()]
        self.use_case = use_cases.ExecuteExistingContractUseCase(self.notifications)
        self.user = baker.make(settings.AUTH_USER_MODEL)
        self.file = SimpleUploadedFile("contract.txt", b"Contract content")
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.DRAFT)

    def tearDown(self):
        try:
            signed_file = Path(self.contract.signed_document.path)
            if signed_file.exists():
                os.remove(str(signed_file.resolve()))
        except ValueError:
            pass

    @patch("sponsors.models.contract.uuid.uuid4", Mock(return_value="1234"))
    def test_execute_and_update_database_object(self):
        self.use_case.execute(self.contract, self.file)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.EXECUTED)
        self.assertEqual(b"Contract content", self.contract.signed_document.read())
        self.assertEqual(f"{Contract.SIGNED_PDF_DIR}1234.txt", self.contract.signed_document.name)

    def test_build_use_case_with_default_notifications(self):
        uc = use_cases.ExecuteExistingContractUseCase.build()
        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(
            uc.notifications[0], ExecutedExistingContractLogger
        )
        self.assertIsInstance(
            uc.notifications[1], RefreshSponsorshipsCache,
        )

    def test_execute_contract_flag_overlapping_sponsorships(self):
        sponsorship = self.contract.sponsorship
        self.use_case.execute(self.contract, self.file)
        self.contract.refresh_from_db()
        recent_contract = baker.make_recipe(
            "sponsors.tests.empty_contract",
            status=Contract.DRAFT,
            sponsorship__sponsor=sponsorship.sponsor,
            sponsorship__start_date=sponsorship.start_date + timedelta(days=5),
            sponsorship__end_date=sponsorship.end_date + timedelta(days=5),
        )

        self.use_case.execute(recent_contract, self.file)
        recent_contract.refresh_from_db()
        sponsorship.refresh_from_db()

        self.assertEqual(recent_contract.status, Contract.EXECUTED)
        self.assertEqual(sponsorship.overlapped_by, recent_contract.sponsorship)

    def test_execute_contract_do_not_flag_overlap_if_no_date_range_conflict(self):
        sponsorship = self.contract.sponsorship
        self.use_case.execute(self.contract, self.file)
        self.contract.refresh_from_db()
        recent_contract = baker.make_recipe(
            "sponsors.tests.empty_contract",
            status=Contract.DRAFT,
            sponsorship__sponsor=sponsorship.sponsor,
            sponsorship__start_date=sponsorship.end_date + timedelta(days=1),
            sponsorship__end_date=sponsorship.end_date + timedelta(days=5),
        )

        self.use_case.execute(recent_contract, self.file)
        recent_contract.refresh_from_db()
        sponsorship.refresh_from_db()

        self.assertEqual(recent_contract.status, Contract.EXECUTED)
        self.assertIsNone(sponsorship.overlapped_by)

    def test_execute_contract_do_not_flag_overlap_if_from_other_sponsor(self):
        sponsorship = self.contract.sponsorship
        self.use_case.execute(self.contract, self.file)
        self.contract.refresh_from_db()
        recent_contract = baker.make_recipe(
            "sponsors.tests.empty_contract",
            status=Contract.DRAFT,
            sponsorship__sponsor=baker.make(Sponsor),
            sponsorship__start_date=sponsorship.start_date + timedelta(days=5),
            sponsorship__end_date=sponsorship.end_date + timedelta(days=5),
        )

        self.use_case.execute(recent_contract, self.file)
        recent_contract.refresh_from_db()
        sponsorship.refresh_from_db()

        self.assertEqual(recent_contract.status, Contract.EXECUTED)
        self.assertIsNone(sponsorship.overlapped_by)


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

    def test_build_use_case_with_default_notificationss(self):
        uc = use_cases.NullifyContractUseCase.build()
        self.assertEqual(len(uc.notifications), 2)
        self.assertIsInstance(
            uc.notifications[0], NullifiedContractLogger
        )
        self.assertIsInstance(
            uc.notifications[1], RefreshSponsorshipsCache,
        )


class SendSponsorshipNotificationUseCaseTests(TestCase):
    def setUp(self):
        self.notifications = [Mock()]
        self.use_case = use_cases.SendSponsorshipNotificationUseCase(self.notifications)
        self.notification = baker.make(SponsorEmailNotificationTemplate)
        self.sponsorships = baker.make(Sponsorship, sponsor__name="Foo", _quantity=3)
        self.sponsorships = Sponsorship.objects.all()  # to respect DB order

    @patch.object(SponsorEmailNotificationTemplate, 'get_email_message')
    def test_send_notifications(self, mock_get_email_message):
        emails = [Mock(EmailMessage, autospec=True) for i in range(3)]
        mock_get_email_message.side_effect = emails
        contact_types = ["administrative"]

        self.use_case.execute(self.notification, self.sponsorships, contact_types, request='request')

        self.assertEqual(mock_get_email_message.call_count, 3)
        self.assertEqual(self.notifications[0].notify.call_count, 3)
        for sponsorship in self.sponsorships:
            kwargs = dict(to_accounting=False, to_administrative=True, to_manager=False, to_primary=False)
            mock_get_email_message.assert_has_calls([call(sponsorship, **kwargs)])
            self.notifications[0].notify.assert_has_calls([
                call(notification=self.notification, sponsorship=sponsorship, contact_types=contact_types, request='request')
            ])
        for email in emails:
            email.send.assert_called_once_with()

    @patch.object(SponsorEmailNotificationTemplate, 'get_email_message', Mock(return_value=None))
    def test_skip_sponsorships_if_no_email_message(self):
        contact_types = ["administrative"]
        self.use_case.execute(self.notification, self.sponsorships, contact_types, request='request')

        self.assertEqual(self.notifications[0].notify.call_count, 0)

    def test_build_use_case_with_default_notificationss(self):
        uc = use_cases.SendSponsorshipNotificationUseCase.build()
        self.assertEqual(len(uc.notifications), 1)
        self.assertIsInstance(
            uc.notifications[0], SendSponsorNotificationLogger
        )


class CloneSponsorshipYearUseCaseTests(TestCase):
    def setUp(self):
        self.request = Mock()
        self.notifications = [Mock()]
        self.use_case = use_cases.CloneSponsorshipYearUseCase(self.notifications)

    def test_clone_package_and_benefits(self):
        baker.make(SponsorshipPackage, year=2021)  # package from another year
        baker.make(SponsorshipPackage, year=2022, _quantity=2)
        baker.make(SponsorshipBenefit, year=2021)  # benefit from another year
        benefits_2022 = baker.make(SponsorshipBenefit, year=2022, _quantity=3)

        created_objects = self.use_case.execute(clone_from_year=2022, target_year=2023, request=self.request)

        # assert new packages were created
        self.assertEqual(5, SponsorshipPackage.objects.count())
        self.assertEqual(2, SponsorshipPackage.objects.filter(year=2022).count())
        self.assertEqual(2, SponsorshipPackage.objects.filter(year=2023).count())
        self.assertEqual(1, SponsorshipPackage.objects.filter(year=2021).count())
        # assert new benefits were created
        self.assertEqual(7, SponsorshipBenefit.objects.count())
        self.assertEqual(3, SponsorshipBenefit.objects.filter(year=2022).count())
        self.assertEqual(3, SponsorshipBenefit.objects.filter(year=2023).count())
        self.assertEqual(1, SponsorshipBenefit.objects.filter(year=2021).count())

        n = self.notifications[0]
        base_kwargs = {"request": self.request, "from_year": 2022}
        self.assertEqual(len(created_objects), n.notify.call_count)
        for resource in created_objects:
            base_kwargs["resource"] = resource
            n.notify.assert_any_call(**base_kwargs)

    def test_build_use_case_with_default_notificationss(self):
        uc = use_cases.CloneSponsorshipYearUseCase.build()
        self.assertEqual(len(uc.notifications), 1)
        self.assertIsInstance(
            uc.notifications[0], ClonedResourcesLogger
        )
