"""Regression coverage for fresh contract documents and retryable delivery."""

import datetime
from smtplib import SMTPException
from tempfile import TemporaryDirectory
from unittest import mock

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from apps.sponsors.exceptions import InvalidStatusError
from apps.sponsors.manage.tests import SponsorshipReviewTestBase
from apps.sponsors.models import Contract


class ContractDeliveryRegressionTests(SponsorshipReviewTestBase):
    def setUp(self):
        super().setUp()
        media_root = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=media_root))
        self.sponsorship.approve(datetime.date(2024, 1, 1), datetime.date(2024, 12, 31))
        self.sponsorship.save()
        self.contract = Contract.new(self.sponsorship)
        self.contract.benefits_list = "- Original benefit"
        self.contract.save()
        for extension in ("pdf", "docx"):
            self.enterContext(
                mock.patch(
                    f"apps.sponsors.contracts.render_contract_to_{extension}_file",
                    side_effect=lambda contract: contract.benefits_list.raw.encode(),
                )
            )
        self.send_url = reverse("manage_contract_send", args=[self.sponsorship.pk])

    def _redraft_with_updated_terms(self):
        self.client.post(reverse("manage_contract_nullify", args=[self.sponsorship.pk]))
        self.client.post(reverse("manage_contract_redraft", args=[self.sponsorship.pk]))
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)
        self.assertFalse(self.contract.document.name)
        self.assertFalse(self.contract.document_docx.name)
        self.contract.benefits_list = "- Updated benefit"
        self.contract.save()
        mail.outbox.clear()

    def test_redraft_clears_stale_documents_and_returns_to_draft(self):
        self.contract.set_final_version(b"old pdf", b"old docx")
        self.contract.nullify()
        self.contract.redraft()
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)
        self.assertFalse(self.contract.document.name)
        self.assertFalse(self.contract.document_docx.name)

    def test_redraft_rejects_a_contract_that_is_not_nullified(self):
        with self.assertRaises(InvalidStatusError):
            self.contract.redraft()
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)

    def test_redraft_then_edit_sends_current_terms_and_finalizes(self):
        self.client.post(self.send_url, {"action": "send_sponsor"})
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)
        old_names = (self.contract.document.name, self.contract.document_docx.name)
        self._redraft_with_updated_terms()

        response = self.client.post(self.send_url, {"action": "send_sponsor"})
        self.assertEqual(response.status_code, 302)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)
        self.assertNotEqual(self.contract.document.name, old_names[0])
        self.assertNotEqual(self.contract.document_docx.name, old_names[1])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0].content, b"- Updated benefit")

    def test_internal_review_uses_current_draft_without_finalizing(self):
        self.contract.set_final_version(b"old pdf", b"old docx")
        self._redraft_with_updated_terms()
        response = self.client.post(
            self.send_url, {"action": "send_internal", "internal_email": "reviewer@pyfound.org"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            [(attachment.filename, attachment.content) for attachment in mail.outbox[0].attachments],
            [("Contract.pdf", b"- Updated benefit"), ("Contract.docx", b"- Updated benefit")],
        )
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)

    def test_render_failure_leaves_contract_draft_and_sends_nothing(self):
        with mock.patch("apps.sponsors.contracts.render_contract_to_pdf_file", side_effect=RuntimeError("render down")):
            response = self.client.post(self.send_url, {"action": "send_sponsor"})
        self.assertEqual(response.status_code, 302)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)
        self.assertFalse(self.contract.document.name)
        self.assertEqual(mail.outbox, [])

    def test_partial_render_preserves_existing_documents_without_sending(self):
        self.contract.set_final_version(b"obsolete pdf", b"obsolete docx")
        Contract.objects.filter(pk=self.contract.pk).update(status=Contract.DRAFT)
        old_names = (self.contract.document.name, self.contract.document_docx.name)
        with mock.patch("apps.sponsors.contracts.render_contract_to_docx_file", return_value=None):
            response = self.client.post(self.send_url, {"action": "send_sponsor"})
        self.assertEqual(response.status_code, 302)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)
        self.assertEqual((self.contract.document.name, self.contract.document_docx.name), old_names)
        self.assertEqual(mail.outbox, [])

    def _assert_failed_send_is_retryable(self, **failure):
        with mock.patch("django.core.mail.EmailMessage.send", **failure):
            response = self.client.post(self.send_url, {"action": "send_sponsor"})
        self.assertEqual(response.status_code, 302)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.DRAFT)
        self.assertFalse(self.contract.document.name)
        self.assertFalse(self.contract.document_docx.name)
        self.assertEqual(mail.outbox, [])

        response = self.client.post(self.send_url, {"action": "send_sponsor"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)

    def test_smtp_failure_rolls_back_finalization_and_allows_retry(self):
        self._assert_failed_send_is_retryable(side_effect=SMTPException("smtp down"))

    def test_zero_delivery_rolls_back_finalization_and_allows_retry(self):
        self._assert_failed_send_is_retryable(return_value=0)

    def test_awaiting_signature_resends_stored_attachment(self):
        self.contract.set_final_version(b"stored PDF snapshot", b"stored DOCX snapshot")
        response = self.client.post(self.send_url, {"action": "send_sponsor"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0].content, b"stored DOCX snapshot")
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.status, Contract.AWAITING_SIGNATURE)
