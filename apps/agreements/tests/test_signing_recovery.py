from smtplib import SMTPException
from typing import cast
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import ERROR, SUCCESS, WARNING, get_messages
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.agreements import workflow
from apps.agreements.models import Agreement, CustomContract, SigningLink
from apps.agreements.tests.test_agreements import PDF, make_officer, offer_contract


class SigningRecoveryTests(TestCase):
    def setUp(self) -> None:
        self.officer = make_officer()
        self.customer = get_user_model().objects.create_user("customer", "customer@example.com", "password")
        self.agreement = offer_contract(self.officer, counterparty_account=self.customer)
        self.client.force_login(self.customer)

    def signature_data(self) -> dict[str, str]:
        return {
            "accept": "on",
            "signer_name": "Customer",
            "signer_title": "Director",
            "document_sha256": self.agreement.document_sha256,
        }

    def test_custom_customer_sign_returns_to_accessible_agreement(self) -> None:
        response = self.client.post(reverse("agreements:sign", args=[self.agreement.pk]), self.signature_data())
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.SIGNED)

    def test_custom_customer_upload_returns_to_accessible_agreement(self) -> None:
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

    def test_custom_customer_withdrawal_keeps_the_record_accessible(self) -> None:
        contract = cast("CustomContract", self.agreement.subject)
        response = self.client.post(reverse("agreements:withdraw", args=[self.agreement.pk]))
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.agreement.refresh_from_db()
        contract.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.WITHDRAWN)
        self.assertIsNone(contract.agreement_id)

    def test_custom_staff_withdrawal_returns_to_the_editable_draft(self) -> None:
        contract = cast("CustomContract", self.agreement.subject)
        self.client.force_login(self.officer)
        response = self.client.post(reverse("agreements:withdraw", args=[self.agreement.pk]))
        self.assertRedirects(response, contract.get_absolute_url())

    def test_failed_invitation_does_not_leave_a_pending_link_and_can_be_retried(self) -> None:
        self.client.force_login(self.officer)
        previous, previous_token = workflow.create_signing_link(
            self.agreement, name="Previous Signer", email="previous@example.com", user=self.officer
        )
        url = reverse("agreements:send_link", args=[self.agreement.pk])
        data = {"name": "Invited Signer", "email": "invited@example.com"}
        with patch(
            "apps.agreements.notifications.EmailMultiAlternatives.send", side_effect=SMTPException("mail unavailable")
        ):
            response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox, [])
        self.assertIn(ERROR, [message.level for message in get_messages(response.wsgi_request)])
        self.assertEqual(list(self.agreement.signing_links.values_list("pk", flat=True)), [previous.pk])
        self.assertTrue(cast("SigningLink", workflow.find_link(previous_token)).is_usable)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.OFFERED)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        sent = self.agreement.signing_links.exclude(pk=previous.pk).get()
        self.assertTrue(sent.is_usable)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [data["email"]])

    def test_empty_recipient_execution_and_resend_do_not_claim_email_delivery(self) -> None:
        self.customer.email = ""
        self.customer.save(update_fields=["email"])
        response = self.client.post(reverse("agreements:sign", args=[self.agreement.pk]), self.signature_data())
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.client.force_login(self.officer)
        response = self.client.post(
            reverse("agreements:countersign", args=[self.agreement.pk]),
            {"name": "Officer", "title": "Director", "accept": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.EXECUTED)
        self.assertEqual(self.agreement.signer_email, "")
        self.assertEqual(mail.outbox, [])
        levels = [message.level for message in get_messages(response.wsgi_request)]
        self.assertIn(WARNING, levels)
        self.assertNotIn(SUCCESS, levels)
        signed_at = self.agreement.countersigned_at

        resend_url = reverse("agreements:resend_executed_copy", args=[self.agreement.pk])
        self.assertNotContains(self.client.get(self.agreement.get_absolute_url()), resend_url)
        response = self.client.post(resend_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mail.outbox, [])
        levels = [message.level for message in get_messages(response.wsgi_request)]
        self.assertIn(WARNING, levels)
        self.assertNotIn(SUCCESS, levels)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.countersigned_at, signed_at)

    def test_delivery_can_be_retried_without_changing_the_countersignature(self) -> None:
        self.client.force_login(self.officer)
        for target, error in (
            ("apps.agreements.notifications.render_pdf", RuntimeError("renderer unavailable")),
            ("apps.agreements.notifications.EmailMultiAlternatives.send", SMTPException("mail unavailable")),
        ):
            with self.subTest(failure=target):
                agreement = offer_contract(self.officer, counterparty_account=self.customer)
                agreement = workflow.sign(
                    agreement,
                    workflow.Signature("Customer", "Director", self.customer.email),
                    seen_sha256=agreement.document_sha256,
                )
                mail.outbox.clear()
                with patch(target, side_effect=error):
                    response = self.client.post(
                        reverse("agreements:countersign", args=[agreement.pk]),
                        {"name": "Officer", "title": "Executive Director", "accept": "on"},
                    )
                self.assertEqual(response.status_code, 302)
                self.assertEqual(mail.outbox, [])
                self.assertIn(ERROR, [message.level for message in get_messages(response.wsgi_request)])
                agreement.refresh_from_db()
                self.assertEqual(agreement.status, Agreement.Status.EXECUTED)
                signed_at = agreement.countersigned_at
                resend_url = reverse("agreements:resend_executed_copy", args=[agreement.pk])
                self.assertContains(self.client.get(agreement.get_absolute_url()), resend_url)
                response = self.client.post(resend_url)
                self.assertEqual(response.status_code, 302)
                agreement.refresh_from_db()
                self.assertEqual(agreement.countersigned_at, signed_at)
                self.assertEqual(agreement.countersigner_name, "Officer")
                self.assertEqual(len(mail.outbox), 1)
                self.assertEqual(mail.outbox[0].to, [self.customer.email])
                self.assertEqual(mail.outbox[0].attachments[0].mimetype, "application/pdf")

    def test_resending_requires_staff_an_executed_agreement_and_post(self) -> None:
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
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertNotContains(self.client.get(agreement.get_absolute_url()), url)
        self.client.logout()
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(mail.outbox, [])

    def test_edit_during_link_submission_refreshes_the_document_and_digest_together(self) -> None:
        link, token = workflow.create_signing_link(
            self.agreement, name="Customer", email=self.customer.email, user=self.officer
        )
        find_link = workflow.find_link

        def edit_after_loading_link(value: str) -> SigningLink | None:
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
            response = self.client.post(url, self.signature_data() | {"signer_name": "Updated Signer"})
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.OFFERED)
        self.assertContains(response, "New clause for review.")
        self.assertEqual(response.context["form"]["document_sha256"].value(), self.agreement.document_sha256)
        self.assertEqual(response.context["form"]["signer_name"].value(), "Updated Signer")
        self.assertEqual(response.context["form"]["signer_title"].value(), "Director")
        self.assertFalse(response.context["form"]["accept"].value())
        response = self.client.post(url, self.signature_data() | {"signer_name": "Updated Signer"})
        self.assertContains(response, "Updated Signer")
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.SIGNED)
        self.assertIsNotNone(SigningLink.objects.get(pk=link.pk).used_at)
