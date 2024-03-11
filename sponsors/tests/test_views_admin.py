import io
import json
import tempfile
import zipfile
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker
from datetime import date, timedelta
from unittest.mock import patch, PropertyMock, Mock

from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core import mail
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse

from .utils import assertMessage, get_static_image_file_as_upload
from ..models import Sponsorship, Contract, SponsorshipBenefit, SponsorBenefit, SponsorEmailNotificationTemplate, \
    GenericAsset, ImgAsset, TextAsset, SponsorshipCurrentYear, SponsorshipPackage
from ..forms import SponsorshipReviewAdminForm, SponsorshipsListForm, SignedSponsorshipReviewAdminForm, \
    SendSponsorshipNotificationForm, CloneApplicationConfigForm
from sponsors.views_admin import send_sponsorship_notifications_action, export_assets_as_zipfile
from sponsors.use_cases import SendSponsorshipNotificationUseCase


class RollbackSponsorshipToEditingAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.APPROVED,
            submited_by=self.user,
            _fill_optional=True,
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_rollback_to_edit", args=[self.sponsorship.pk]
        )

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(
            response, "sponsors/admin/rollback_sponsorship_to_editing.html"
        )
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPLIED
        )  # did not update

    def test_rollback_sponsorship_to_applied_on_post(self):
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship is now editable!", messages.SUCCESS)

    def test_do_not_rollback_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(
            response, "sponsors/admin/rollback_sponsorship_to_editing.html"
        )
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPLIED
        )  # did not update

        response = self.client.post(self.url, data={"confirm": "invalid"})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(
            response, "sponsors/admin/rollback_sponsorship_to_editing.html"
        )
        self.assertNotEqual(self.sponsorship.status, Sponsorship.APPLIED)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_rejecting_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(
            msg, "Can't rollback to edit a Finalized sponsorship.", messages.ERROR
        )


class RejectedSponsorshipAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship,
            status=Sponsorship.APPLIED,
            submited_by=self.user,
            _fill_optional=True,
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_reject", args=[self.sponsorship.pk]
        )

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(response, "sponsors/admin/reject_application.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.REJECTED
        )  # did not update

    def test_reject_sponsorship_on_post(self):
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertTrue(mail.outbox)
        self.assertEqual(self.sponsorship.status, Sponsorship.REJECTED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship was rejected!", messages.SUCCESS)

    def test_do_not_reject_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/reject_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.REJECTED
        )  # did not update

        response = self.client.post(self.url, data={"confirm": "invalid"})
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/reject_application.html")
        self.assertNotEqual(self.sponsorship.status, Sponsorship.REJECTED)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_rejecting_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        data = {"confirm": "yes"}
        response = self.client.post(self.url, data=data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Can't reject a Finalized sponsorship.", messages.ERROR)


class ApproveSponsorshipAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship, status=Sponsorship.APPLIED, _fill_optional=True
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_approve", args=[self.sponsorship.pk]
        )
        today = date.today()
        self.package = baker.make("sponsors.SponsorshipPackage")
        self.data = {
            "confirm": "yes",
            "start_date": today,
            "end_date": today + timedelta(days=100),
            "package": self.package.pk,
            "sponsorship_fee": 500,
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        form = context["form"]
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertIsInstance(form, SponsorshipReviewAdminForm)
        self.assertEqual(form.initial["package"], self.sponsorship.package)
        self.assertEqual(form.initial["start_date"], self.sponsorship.start_date)
        self.assertEqual(form.initial["end_date"], self.sponsorship.end_date)
        self.assertEqual(
            form.initial["sponsorship_fee"], self.sponsorship.sponsorship_fee
        )
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

    def test_approve_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)

        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Sponsorship was approved!", messages.SUCCESS)

    def test_do_not_approve_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(self.sponsorship.status, Sponsorship.APPROVED)

    def test_do_not_approve_if_form_with_invalid_data(self):
        self.data = {"confirm": "yes"}
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update
        self.assertTrue(response.context["form"].errors)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_approving_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Can't approve a Finalized sponsorship.", messages.ERROR)


class ApproveSignedSponsorshipAdminViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsorship = baker.make(
            Sponsorship, status=Sponsorship.APPLIED, _fill_optional=True
        )
        self.url = reverse(
            "admin:sponsors_sponsorship_approve_existing_contract", args=[self.sponsorship.pk]
        )
        today = date.today()
        self.package = baker.make("sponsors.SponsorshipPackage")
        self.data = {
            "confirm": "yes",
            "start_date": today,
            "end_date": today + timedelta(days=100),
            "package": self.package.pk,
            "sponsorship_fee": 500,
            "signed_contract": io.BytesIO(b"Signed contract")
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context
        form = context["form"]
        self.sponsorship.refresh_from_db()

        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertEqual(context["sponsorship"], self.sponsorship)
        self.assertIsInstance(form, SignedSponsorshipReviewAdminForm)
        self.assertEqual(form.initial["package"], self.sponsorship.package)
        self.assertEqual(form.initial["start_date"], self.sponsorship.start_date)
        self.assertEqual(form.initial["end_date"], self.sponsorship.end_date)
        self.assertEqual(
            form.initial["sponsorship_fee"], self.sponsorship.sponsorship_fee
        )
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

    def test_approve_sponsorship_and_execute_contract_on_post(self):
        response = self.client.post(self.url, data=self.data)

        self.sponsorship.refresh_from_db()
        contract = self.sponsorship.contract

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        self.assertEqual(contract.status, Contract.EXECUTED)
        self.assertEqual(contract.signed_document.read(), b"Signed contract")
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Signed sponsorship was approved!", messages.SUCCESS)

    def test_do_not_approve_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(self.sponsorship.status, Sponsorship.APPROVED)

    def test_do_not_approve_if_form_with_invalid_data(self):
        self.data = {"confirm": "yes"}
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/approve_application.html")
        self.assertNotEqual(
            self.sponsorship.status, Sponsorship.APPROVED
        )  # did not update
        self.assertTrue(response.context["form"].errors)

    def test_404_if_sponsorship_does_not_exist(self):
        self.sponsorship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_message_user_if_approving_invalid_sponsorship(self):
        self.sponsorship.status = Sponsorship.FINALIZED
        self.sponsorship.save()
        response = self.client.post(self.url, data=self.data)
        self.sponsorship.refresh_from_db()

        expected_url = reverse(
            "admin:sponsors_sponsorship_change", args=[self.sponsorship.pk]
        )
        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Can't approve a Finalized sponsorship.", messages.ERROR)


class SendContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract")
        self.url = reverse(
            "admin:sponsors_contract_send", args=[self.contract.pk]
        )
        self.data = {
            "confirm": "yes",
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/send_contract.html")
        self.assertEqual(context["contract"], self.contract)

    @patch.object(
        Sponsorship, "verified_emails", PropertyMock(return_value=["email@email.com"])
    )
    def test_approve_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )
        self.contract.refresh_from_db()

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertTrue(self.contract.document.name)
        self.assertEqual(1, len(mail.outbox))
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "Contract was sent!", messages.SUCCESS)

    @patch.object(
        Sponsorship, "verified_emails", PropertyMock(return_value=["email@email.com"])
    )
    def test_display_error_message_to_user_if_invalid_status(self):
        self.contract.status = Contract.AWAITING_SIGNATURE
        self.contract.save()
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )

        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(0, len(mail.outbox))
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(
            msg,
            "Contract with status Awaiting Signature can't be sent.",
            messages.ERROR,
        )

    def test_do_not_send_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/send_contract.html")
        self.assertFalse(self.contract.document.name)

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "sponsors/admin/send_contract.html")
        self.assertFalse(self.contract.document.name)
        self.assertEqual(0, len(mail.outbox))

    def test_404_if_contract_does_not_exist(self):
        self.contract.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)


class ExecuteContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE)
        self.url = reverse(
            "admin:sponsors_contract_execute", args=[self.contract.pk]
        )
        self.data = {
            "confirm": "yes",
            "signed_document": SimpleUploadedFile("contract.txt", b"Contract content"),
        }

    def tearDown(self):
        try:
            self.contract.refresh_from_db()
            if self.contract.signed_document:
                self.contract.signed_document.delete()
        except Contract.DoesNotExist:
            pass

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.assertEqual(context["contract"], self.contract)

    def test_execute_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.EXECUTED)
        assertMessage(msg, "Contract was executed!", messages.SUCCESS)

    def test_display_error_message_to_user_if_invalid_status(self):
        self.contract.status = Contract.OUTDATED
        self.contract.save()
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )

        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.OUTDATED)
        assertMessage(
            msg,
            "Contract with status Outdated can't be executed.",
            messages.ERROR,
        )

    def test_do_not_execute_contract_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

    def test_display_error_message_to_user_if_no_signed_document(self):
        self.data.pop("signed_document")
        response = self.client.post(self.url, data=self.data)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/execute_contract.html")
        self.assertEqual(context["contract"], self.contract)
        self.assertTrue(context["error_msg"])

    def test_404_if_contract_does_not_exist(self):
        self.contract.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)


class NullifyContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe("sponsors.tests.empty_contract", status=Contract.AWAITING_SIGNATURE)
        self.url = reverse(
            "admin:sponsors_contract_nullify", args=[self.contract.pk]
        )
        self.data = {
            "confirm": "yes",
        }

    def test_display_confirmation_form_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/nullify_contract.html")
        self.assertEqual(context["contract"], self.contract)

    def test_nullify_sponsorship_on_post(self):
        response = self.client.post(self.url, data=self.data)
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.NULLIFIED)
        assertMessage(msg, "Contract was nullified!", messages.SUCCESS)

    def test_display_error_message_to_user_if_invalid_status(self):
        self.contract.status = Contract.DRAFT
        self.contract.save()
        expected_url = reverse(
            "admin:sponsors_contract_change", args=[self.contract.pk]
        )

        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        msg = list(get_messages(response.wsgi_request))[0]

        self.assertRedirects(response, expected_url, fetch_redirect_response=True)
        self.assertEqual(self.contract.status, Contract.DRAFT)
        assertMessage(
            msg,
            "Contract with status Draft can't be nullified.",
            messages.ERROR,
        )

    def test_do_not_nullify_contract_if_no_confirmation_in_the_post(self):
        self.data.pop("confirm")
        response = self.client.post(self.url, data=self.data)
        self.contract.refresh_from_db()
        self.assertTemplateUsed(response, "sponsors/admin/nullify_contract.html")
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

        self.data["confirm"] = "invalid"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "sponsors/admin/nullify_contract.html")
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

    def test_404_if_contract_does_not_exist(self):
        self.contract.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)


class UpdateRelatedSponsorshipsTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.benefit = baker.make(SponsorshipBenefit)
        self.sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship_benefit=self.benefit,
            sponsorship__sponsor__name="Foo",
            added_by_user=True,  # to make sure we keep previous fields
        )
        self.url = reverse(
            "admin:sponsors_sponsorshipbenefit_update_related", args=[self.benefit.pk]
        )
        self.data = {"sponsorships": [self.sponsor_benefit.sponsorship.pk]}

    def test_display_form_from_benefit_on_get(self):
        response = self.client.get(self.url)
        context = response.context

        self.assertTemplateUsed(response, "sponsors/admin/update_related_sponsorships.html")
        self.assertEqual(context["benefit"], self.benefit)
        self.assertIsInstance(context["form"], SponsorshipsListForm)
        self.assertEqual(context["form"].sponsorship_benefit, self.benefit)

    def test_list_related_sponsorships_with_initial(self):
        baker.make(Sponsorship)  # unrelated-sponsorship
        other_sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship_benefit=self.benefit,
            sponsorship__sponsor__name="Bar",
        )

        response = self.client.get(self.url)
        initial = response.context["form"].initial

        self.assertEqual(2, len(initial["sponsorships"]))
        self.assertIn(self.sponsor_benefit.sponsorship.pk, initial["sponsorships"])
        self.assertIn(other_sponsor_benefit.sponsorship.pk, initial["sponsorships"])

    def test_bad_request_if_invalid_post_data(self):
        self.data["sponsorships"] = []

        response = self.client.post(self.url, data=self.data)

        self.assertTrue(response.context["form"].errors)

    def test_redirect_back_to_benefit_page_if_success(self):
        redirect_url = reverse(
            "admin:sponsors_sponsorshipbenefit_change", args=[self.benefit.pk]
        )
        response = self.client.post(self.url, data=self.data)

        self.assertRedirects(response, redirect_url)
        msg = list(get_messages(response.wsgi_request))[0]
        assertMessage(msg, "1 related sponsorships updated!", messages.SUCCESS)

    def test_update_selected_sponsorships_only(self):
        other_sponsor_benefit = baker.make(
            SponsorBenefit,
            sponsorship_benefit=self.benefit,
            sponsorship__sponsor__name="Bar",
            name=self.benefit.name,
            description=self.benefit.description,
        )
        prev_name, prev_description = self.benefit.name, self.benefit.description
        self.benefit.name = 'New name'
        self.benefit.description = 'New description'
        self.benefit.save()

        response = self.client.post(self.url, data=self.data)

        self.sponsor_benefit.refresh_from_db()
        self.assertEqual(self.sponsor_benefit.name, "New name")
        self.assertEqual(self.sponsor_benefit.description, "New description")
        self.assertTrue(self.sponsor_benefit.added_by_user)
        # make sure sponsor benefit from unselected sponsorships wasn't deleted
        other_sponsor_benefit.refresh_from_db()
        self.assertEqual(other_sponsor_benefit.name, prev_name)
        self.assertEqual(other_sponsor_benefit.description, prev_description)

    def test_404_if_benefit_does_not_exist(self):
        self.benefit.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)


class PreviewContractViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.contract = baker.make_recipe(
            "sponsors.tests.empty_contract", sponsorship__start_date=date.today()
        )
        self.url = reverse(
            "admin:sponsors_contract_preview", args=[self.contract.pk]
        )

    @patch("sponsors.views_admin.render_contract_to_pdf_response")
    def test_render_pdf_by_default(self, mocked_render):
        response = HttpResponse()
        mocked_render.return_value = response

        r = self.client.get(self.url)

        self.assertEqual(r, response)
        self.assertEqual(r.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(mocked_render.call_count, 1)
        self.assertEqual(mocked_render.call_args[0][1], self.contract)
        self.assertIsInstance(mocked_render.call_args[0][0], WSGIRequest)

    @patch("sponsors.views_admin.render_contract_to_docx_response")
    def test_render_docx_if_specified_in_the_querystring(self, mocked_render):
        response = HttpResponse()
        mocked_render.return_value = response

        r = self.client.get(self.url + "?format=docx")

        self.assertEqual(r, response)
        self.assertEqual(r.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(mocked_render.call_count, 1)
        self.assertEqual(mocked_render.call_args[0][1], self.contract)
        self.assertIsInstance(mocked_render.call_args[0][0], WSGIRequest)


class PreviewSponsorEmailNotificationTemplateTests(TestCase):
    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.sponsor_notification = baker.make(SponsorEmailNotificationTemplate, content="{{'content'|upper}}")
        self.url = self.sponsor_notification.preview_content_url

    def test_display_content_on_response(self):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(b"CONTENT", response.content)

    def test_404_if_template_does_not_exist(self):
        self.sponsor_notification.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)

        r = self.client.get(self.url)

        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)


class ClonsSponsorshipYearConfigurationTests(TestCase):

    def setUp(self):
        self.user = baker.make(
            settings.AUTH_USER_MODEL, is_staff=True, is_superuser=True
        )
        self.client.force_login(self.user)
        self.url = reverse("admin:sponsors_sponsorshipcurrentyear_clone")

    def test_login_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.client.logout()
        r = self.client.get(self.url)
        self.assertRedirects(r, redirect_url)

    def test_staff_required(self):
        login_url = reverse("admin:login")
        redirect_url = f"{login_url}?next={self.url}"
        self.user.is_staff = False
        self.user.save()
        self.client.force_login(self.user)
        r = self.client.get(self.url)
        self.assertRedirects(r, redirect_url, fetch_redirect_response=False)

    def test_correct_template_and_form_on_get(self):
        baker.make(SponsorshipBenefit, year=2022)
        baker.make(SponsorshipPackage, year=2023)
        response = self.client.get(self.url)

        template = "sponsors/admin/clone_application_config_form.html"
        curr_year = SponsorshipCurrentYear.get_year()

        self.assertTemplateUsed(response, template)
        self.assertIsInstance(response.context["form"], CloneApplicationConfigForm)
        self.assertEqual(response.context["current_year"], curr_year)
        self.assertEqual(response.context["configured_years"], [2023, 2022])
        self.assertIsNone(response.context["new_year"])

    def test_display_form_errors_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.context["form"].errors)

    def test_clone_sponsorship_application_config_with_valid_post(self):
        baker.make(SponsorshipBenefit, year=2022)
        data = {"from_year": 2022, "target_year": 2023}
        response = self.client.post(self.url, data=data)

        self.assertEqual(SponsorshipBenefit.objects.from_year(2022).count(), 1)
        self.assertEqual(SponsorshipBenefit.objects.from_year(2023).count(), 1)
        template = "sponsors/admin/clone_application_config_form.html"
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.context["new_year"], 2023)
        self.assertEqual(response.context["configured_years"], [2023, 2022])


#######################
### TEST CUSTOM ACTIONS
class SendSponsorshipNotificationTests(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        baker.make(Sponsorship, _quantity=3, sponsor__name='foo')
        self.sponsorship = Sponsorship.objects.all()[0]
        baker.make('sponsors.EmailTargetable', sponsor_benefit__sponsorship=self.sponsorship)
        self.queryset = Sponsorship.objects.all()
        self.user = baker.make("users.User")

    @patch("sponsors.views_admin.render")
    def test_render_template_and_context_as_expected(self, mocked_render):
        mocked_render.return_value = "HTTP Response"
        request = self.request_factory.post("/", data={})
        request.user = self.user

        resp = send_sponsorship_notifications_action(Mock(), request, self.queryset)

        self.assertEqual("HTTP Response", resp)
        self.assertEqual(1, mocked_render.call_count)
        ret_request, template = mocked_render.call_args[0]
        context = mocked_render.call_args[1]["context"]
        self.assertEqual(request, request)
        self.assertEqual("sponsors/admin/send_sponsors_notification.html", template)
        self.assertEqual([self.sponsorship], list(context["to_notify"]))
        self.assertEqual(2, len(context["to_ignore"]))
        self.assertNotIn(self.sponsorship, context["to_ignore"])
        self.assertIsInstance(context["form"], SendSponsorshipNotificationForm)

    @patch("sponsors.views_admin.render")
    def test_render_form_error_if_invalid(self, mocked_render):
        mocked_render.return_value = "HTTP Response"
        request = self.request_factory.post("/", data={"confirm": "yes"})
        request.user = self.user

        resp = send_sponsorship_notifications_action(Mock(), request, self.queryset)
        context = mocked_render.call_args[1]["context"]
        form = context["form"]

        self.assertIn("contact_types", form.errors)

    @patch.object(SendSponsorshipNotificationUseCase, "build")
    def test_call_use_case_and_redirect_with_success(self, mock_build):
        notification = baker.make("SponsorEmailNotificationTemplate")
        mocked_uc = Mock(SendSponsorshipNotificationUseCase, autospec=True)
        mock_build.return_value = mocked_uc
        data = {"confirm": "yes", "notification": notification.pk, "contact_types": ["primary"]}
        request = self.request_factory.post("/", data=data)
        request.user = self.user

        resp = send_sponsorship_notifications_action(Mock(), request, self.queryset)
        expected_url = reverse("admin:sponsors_sponsorship_changelist")

        self.assertEqual(302, resp.status_code)
        self.assertEqual(expected_url, resp["Location"])
        mock_build.assert_called_once_with()
        self.assertEqual(1, mocked_uc.execute.call_count)
        kwargs = mocked_uc.execute.call_args[1]
        self.assertEqual(request, kwargs["request"])
        self.assertEqual(notification, kwargs["notification"])
        self.assertEqual(list(self.queryset), list(kwargs["sponsorships"]))
        self.assertEqual(["primary"], kwargs["contact_types"])


class ExportAssetsAsZipTests(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get("/")
        self.request.user = baker.make("users.User")
        self.sponsorship = baker.make(Sponsorship, sponsor__name='Sponsor Name')
        self.ModelAdmin = Mock()
        self.text_asset = TextAsset.objects.create(
            uuid=uuid4(),
            content_object=self.sponsorship,
            internal_name="text_input",
        )
        self.img_asset = ImgAsset.objects.create(
            uuid=uuid4(),
            content_object=self.sponsorship.sponsor,
            internal_name="img_input",
        )

    def test_display_same_page_with_warning_message_if_no_query(self):
        queryset = GenericAsset.objects.none()
        response = export_assets_as_zipfile(self.ModelAdmin, self.request, queryset)

        self.assertEqual(302, response.status_code)
        self.assertEqual(self.request.path, response["Location"])
        msg = "You have to select at least one asset to export."
        self.ModelAdmin.message_user.assert_called_once_with(self.request, msg, messages.WARNING)

    def test_display_same_page_with_warning_message_if_any_asset_without_value(self):
        self.text_asset.value = "Foo"
        self.text_asset.save()

        queryset = GenericAsset.objects.all()
        response = export_assets_as_zipfile(self.ModelAdmin, self.request, queryset)

        self.assertEqual(302, response.status_code)
        self.assertEqual(self.request.path, response["Location"])
        msg = "1 assets from the selection doesn't have data to export. Please review your selection!"
        self.ModelAdmin.message_user.assert_called_once_with(self.request, msg, messages.WARNING)

    def test_response_is_configured_to_be_zip_file(self):
        self.text_asset.value = "foo"
        self.img_asset.value = SimpleUploadedFile(name='test_image.jpg', content=b"content", content_type='image/jpeg')
        self.text_asset.save()
        self.img_asset.save()

        queryset = GenericAsset.objects.all()
        response = export_assets_as_zipfile(self.ModelAdmin, self.request, queryset)

        self.assertEqual("application/x-zip-compressed", response["Content-Type"])
        self.assertEqual("attachment; filename=assets.zip", response["Content-Disposition"])

    def test_zip_file_organize_assets_within_sponsors_directories(self):
        self.text_asset.value = "foo"
        self.img_asset.value = get_static_image_file_as_upload("psf-logo.png")
        self.text_asset.save()
        self.img_asset.save()

        queryset = GenericAsset.objects.all()
        response = export_assets_as_zipfile(self.ModelAdmin, self.request, queryset)
        content = io.BytesIO(response.content)

        with zipfile.ZipFile(content, "r") as zip_file:
            self.assertEqual(2, len(zip_file.infolist()))
            with zip_file.open("Sponsor Name/text_input.txt") as cur_file:
                self.assertEqual("foo", cur_file.read().decode())
            with zip_file.open("Sponsor Name/img_input.png") as cur_file:
                self.assertEqual(self.img_asset.value.read(), cur_file.read())
