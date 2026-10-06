from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.agreements import workflow
from apps.agreements.models import Agreement, SigningLink
from apps.agreements.tests.test_agreements import PDF, make_officer, offer_contract


class SigningRecoveryTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.customer = get_user_model().objects.create_user("customer", "customer@example.com", "password")
        self.agreement = offer_contract(self.officer, counterparty_account=self.customer)
        self.client.force_login(self.customer)

    def signature_data(self):
        return {
            "accept": "on",
            "signer_name": "Customer",
            "signer_title": "Director",
            "document_sha256": self.agreement.document_sha256,
        }

    def test_custom_customer_sign_returns_to_accessible_agreement(self):
        response = self.client.post(reverse("agreements:sign", args=[self.agreement.pk]), self.signature_data())
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.SIGNED)

    def test_custom_customer_upload_returns_to_accessible_agreement(self):
        response = self.client.post(
            reverse("agreements:record_copy", args=[self.agreement.pk]),
            {
                "signed_copy": SimpleUploadedFile("signed.pdf", PDF, content_type="application/pdf"),
                "signer_name": "Customer",
                "signer_title": "Director",
                "signer_email": self.customer.email,
                "signed_on": "2026-09-01",
                "matches": "on",
                "document_sha256": self.agreement.document_sha256,
            },
        )
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.signature_method, Agreement.SignatureMethod.OFFLINE)

    def test_custom_customer_withdrawal_keeps_the_record_accessible(self):
        contract = self.agreement.subject
        response = self.client.post(reverse("agreements:withdraw", args=[self.agreement.pk]))
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.agreement.refresh_from_db()
        contract.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.WITHDRAWN)
        self.assertIsNone(contract.agreement_id)

    def test_custom_staff_withdrawal_returns_to_the_editable_draft(self):
        contract = self.agreement.subject
        self.client.force_login(self.officer)
        response = self.client.post(reverse("agreements:withdraw", args=[self.agreement.pk]))
        self.assertRedirects(response, contract.get_absolute_url())

    def test_delivery_can_be_retried_without_changing_the_countersignature(self):
        self.client.force_login(self.officer)
        for target, error in (
            ("apps.agreements.notifications.render_pdf", RuntimeError("renderer unavailable")),
            ("apps.agreements.notifications.EmailMessage.send", SMTPException("mail unavailable")),
        ):
            with self.subTest(failure=target):
                agreement = offer_contract(self.officer, counterparty_account=self.customer)
                agreement = workflow.sign(
                    agreement,
                    workflow.Signature("Customer", "Director", self.customer.email),
                    seen_sha256=agreement.document_sha256,
                )
                with patch(target, side_effect=error), self.assertLogs("apps.agreements.views.signing", level="ERROR"):
                    response = self.client.post(
                        reverse("agreements:countersign", args=[agreement.pk]),
                        {"name": "Officer", "title": "Executive Director", "accept": "on"},
                    )
                self.assertEqual(response.status_code, 302)
                agreement.refresh_from_db()
                self.assertEqual(agreement.status, Agreement.Status.EXECUTED)
                signed_at = agreement.countersigned_at
                resend_url = reverse("agreements:resend_executed_copy", args=[agreement.pk])
                self.assertContains(self.client.get(agreement.get_absolute_url()), resend_url)
                mail.outbox.clear()
                response = self.client.post(resend_url)
                self.assertEqual(response.status_code, 302)
                agreement.refresh_from_db()
                self.assertEqual(agreement.countersigned_at, signed_at)
                self.assertEqual(agreement.countersigner_name, "Officer")
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(mail.outbox[0].to, [self.customer.email])
                self.assertEqual(mail.outbox[0].attachments[0].mimetype, "application/pdf")

    def test_resending_requires_staff_an_executed_agreement_and_post(self):
        agreement = workflow.sign(
            self.agreement,
            workflow.Signature("Customer", "Director", self.customer.email),
            seen_sha256=self.agreement.document_sha256,
        )
        self.client.force_login(self.officer)
        url = reverse("agreements:resend_executed_copy", args=[agreement.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        agreement = workflow.countersign(agreement, user=self.officer, name="Officer", title="Director")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertNotContains(self.client.get(agreement.get_absolute_url()), url)
        self.client.logout()
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(mail.outbox, [])

    def test_edit_during_link_submission_refreshes_the_document_and_digest_together(self):
        link, token = workflow.create_signing_link(
            self.agreement, name="Customer", email=self.customer.email, user=self.officer
        )
        find_link = workflow.find_link

        def edit_after_loading_link(value):
            loaded = find_link(value)
            workflow.edit(
                self.agreement,
                markdown=self.agreement.document_markdown + "\nNew clause for review.",
                note="Amended terms",
                user=self.officer,
                base_sha256=self.agreement.document_sha256,
            )
            return loaded

        self.client.logout()
        url = reverse("agreements:sign_link", args=[token])
        with patch("apps.agreements.workflow.find_link", side_effect=edit_after_loading_link):
            response = self.client.post(url, self.signature_data())
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.OFFERED)
        self.assertContains(response, "New clause for review.")
        self.assertEqual(response.context["form"]["document_sha256"].value(), self.agreement.document_sha256)
        self.client.post(url, self.signature_data())
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.SIGNED)
        self.assertIsNotNone(SigningLink.objects.get(pk=link.pk).used_at)
