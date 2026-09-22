"""Regression coverage for contract reuse, locked edits, and failed-send retries."""

import datetime
from smtplib import SMTPException
from tempfile import TemporaryDirectory
from unittest import mock

from django.core import mail
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.sponsors import use_cases
from apps.sponsors.exceptions import InvalidStatusError
from apps.sponsors.manage.tests import SponsorshipReviewTestBase
from apps.sponsors.models import Contract, SponsorBenefit, SponsorContact, Sponsorship


class ManageContractRegressionTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        media_root = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=media_root))
        SponsorBenefit.new_copy(self.benefit, sponsorship=self.sponsorship)
        self.contract = Contract.new(self.sponsorship)
        self.approval_data = {
            "start_date": datetime.date(2024, 1, 1),
            "end_date": datetime.date(2024, 12, 31),
            "package": self.package.pk,
            "sponsorship_fee": 150000,
        }

    def _post_approval(self, *, signed=False, **overrides):
        payload = {**self.approval_data, **overrides}
        if signed:
            payload["signed_contract"] = SimpleUploadedFile("signed.pdf", b"signed-bytes")
        route = "manage_sponsorship_approve_signed" if signed else "manage_sponsorship_approve"
        return self.client.post(reverse(route, args=[self.sponsorship.pk]), payload)

    def _approve(self):
        self.sponsorship.approve(self.approval_data["start_date"], self.approval_data["end_date"])
        self.sponsorship.save()

    def _assert_same_contract(self, status):
        self.contract.refresh_from_db()
        self.assertEqual(Contract.objects.get(sponsorship=self.sponsorship).pk, self.contract.pk)
        self.assertEqual(self.contract.status, status)

    def test_approval_reuses_composer_draft(self):
        original_terms = self.contract.benefits_list.raw
        response = self._post_approval()
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        self._assert_same_contract(Contract.DRAFT)
        self.assertEqual(self.contract.benefits_list.raw, original_terms)

    def test_approval_preserves_awaiting_signature_documents(self):
        self.contract.set_final_version(b"existing pdf", b"existing docx")
        original_names = (self.contract.document.name, self.contract.document_docx.name)
        response = self._post_approval(sponsorship_fee=200000)
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.sponsorship_fee, 200000)
        self._assert_same_contract(Contract.AWAITING_SIGNATURE)
        self.assertEqual((self.contract.document.name, self.contract.document_docx.name), original_names)

    def test_approval_preserves_zero_fee(self):
        response = self._post_approval(sponsorship_fee=0)
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        self.assertEqual(self.sponsorship.sponsorship_fee, 0)

    def _assert_stale_approval_rejected(self, status):
        use_case = use_cases.ApproveSponsorshipApplicationUseCase([])
        data = {**self.approval_data, "package": self.package}
        approved = use_case.execute(self.sponsorship, **data)
        self.contract = approved.contract
        if status == Contract.AWAITING_SIGNATURE:
            self.contract.set_final_version(b"existing pdf", b"existing docx")
        elif status == Contract.EXECUTED:
            use_cases.ExecuteExistingContractUseCase([]).execute(
                self.contract, SimpleUploadedFile("signed.pdf", b"signed-bytes")
            )
        documents = (self.contract.document.name, self.contract.signed_document.name)
        # The caller still holds the pre-approval sponsorship instance.
        with self.assertRaises(InvalidStatusError):
            use_case.execute(self.sponsorship, **data)
        self.assertEqual(Contract.objects.filter(sponsorship=approved).count(), 1)
        self._assert_same_contract(status)
        self.assertEqual((self.contract.document.name, self.contract.signed_document.name), documents)

    def test_stale_approval_cannot_duplicate_draft(self):
        self._assert_stale_approval_rejected(Contract.DRAFT)

    def test_stale_approval_preserves_awaiting_signature_contract(self):
        self._assert_stale_approval_rejected(Contract.AWAITING_SIGNATURE)

    def test_stale_approval_preserves_executed_contract(self):
        self._assert_stale_approval_rejected(Contract.EXECUTED)

    def test_signed_upload_failure_rolls_back_approval(self):
        with (
            mock.patch.object(FileSystemStorage, "_save", side_effect=OSError("disk full")),
            self.assertRaises(OSError),
        ):
            self._post_approval(signed=True, sponsorship_fee=100)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPLIED)
        self.assertFalse(self.sponsorship.locked)
        self.assertEqual(self.sponsorship.sponsorship_fee, 150000)
        self._assert_same_contract(Contract.DRAFT)
        self.assertFalse(self.contract.signed_document)

    def test_stale_signed_approval_preserves_draft(self):
        self._approve()
        response = self._post_approval(signed=True, sponsorship_fee=100)
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.APPROVED)
        self.assertEqual(self.sponsorship.sponsorship_fee, 150000)
        self._assert_same_contract(Contract.DRAFT)
        self.assertFalse(self.contract.signed_document)

    def test_signed_approval_executes_existing_draft(self):
        response = self._post_approval(signed=True)
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        self._assert_same_contract(Contract.EXECUTED)

    def test_stale_signed_approval_preserves_executed_document(self):
        self._approve()
        self.contract.signed_document = SimpleUploadedFile("existing.pdf", b"already-signed")
        self.contract.execute(force=True)
        response = self._post_approval(signed=True)
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.status, Sponsorship.FINALIZED)
        self._assert_same_contract(Contract.EXECUTED)
        with self.contract.signed_document.open("rb") as document:
            self.assertEqual(document.read(), b"already-signed")

    def _assert_locked_edit_rejected(self):
        response = self.client.post(
            reverse("manage_sponsorship_edit", args=[self.sponsorship.pk]),
            {"package": self.package.pk, "sponsorship_fee": 999999, "year": self.year},
        )
        self.assertEqual(response.status_code, 302)
        self.sponsorship.refresh_from_db()
        self.assertEqual(self.sponsorship.sponsorship_fee, 150000)

    def test_locked_approved_sponsorship_cannot_be_edited(self):
        self._approve()
        self._assert_locked_edit_rejected()

    def test_finalized_sponsorship_cannot_be_edited(self):
        self._approve()
        self.contract.execute(force=True)
        self._assert_locked_edit_rejected()

    def test_locked_sponsorship_contract_cannot_be_regenerated(self):
        self._approve()
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self._assert_same_contract(Contract.DRAFT)

    def test_executed_contract_cannot_be_regenerated_even_if_unlocked(self):
        self._approve()
        self.contract.execute(force=True)
        self.sponsorship.locked = False
        self.sponsorship.save(update_fields=["locked"])
        response = self.client.post(reverse("manage_contract_regenerate", args=[self.sponsorship.pk]))
        self.assertEqual(response.status_code, 302)
        self._assert_same_contract(Contract.EXECUTED)

    def _open_composer(self):
        SponsorContact.objects.create(sponsor=self.sponsor, name="Jane Doe", email="jane@acme.com", primary=True)
        session = self.client.session
        session["composer"] = {"sponsorship_id": self.sponsorship.pk, "contract_id": self.contract.pk}
        session.save()
        return reverse("manage_composer") + "?step=6"

    @mock.patch("apps.sponsors.contracts.render_contract_to_docx_file", return_value=b"docx-bytes")
    @mock.patch("apps.sponsors.contracts.render_contract_to_pdf_file", return_value=b"pdf-bytes")
    def test_composer_delivery_failure_preserves_draft_and_session_for_retry(self, mock_pdf, mock_docx):
        url = self._open_composer()
        payload = {"action": "send_proposal", "email_subject": "Contract", "email_body": "Please sign."}
        with mock.patch("django.core.mail.EmailMessage.send", side_effect=SMTPException("smtp down")):
            response = self.client.post(url, payload)
        self.assertRedirects(response, url, fetch_redirect_response=False)
        self.assertIn("composer", self.client.session)
        self._assert_same_contract(Contract.DRAFT)
        self.assertEqual(mail.outbox, [])

        response = self.client.post(url, payload)
        self.assertRedirects(
            response, reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]), fetch_redirect_response=False
        )
        self.assertEqual(len(mail.outbox), 1)
        self._assert_same_contract(Contract.AWAITING_SIGNATURE)
        self.assertNotIn("composer", self.client.session)

    def test_stale_composer_cannot_edit_finalized_contract(self):
        url = self._open_composer()
        original_terms = (self.contract.sponsor_info, self.contract.benefits_list.raw)
        self._approve()
        self.contract.signed_document = SimpleUploadedFile("signed.pdf", b"signed-bytes")
        self.contract.execute(force=True)
        response = self.client.post(
            url,
            {"action": "save_contract", "sponsor_info": "Tampered", "benefits_list": "- Tampered", "legal_clauses": ""},
        )
        self.assertRedirects(
            response, reverse("manage_sponsorship_detail", args=[self.sponsorship.pk]), fetch_redirect_response=False
        )
        self._assert_same_contract(Contract.EXECUTED)
        self.assertEqual((self.contract.sponsor_info, self.contract.benefits_list.raw), original_terms)
