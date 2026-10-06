from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from apps.agreements import documents, notifications
from apps.agreements.models import Agreement, SignedCopy
from apps.agreements.tests.test_agreements import make_officer, offer_contract


class SignedDocumentTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.agreement = offer_contract(
            self.officer,
            counterparty_name="Example ![logo](https://example.com/logo.png) **LLC**",
        )
        self.agreement.signer_name = "Grace Hopper"
        self.agreement.signer_title = "CTO"
        self.agreement.signer_email = "grace@example.com"
        self.agreement.signed_at = timezone.now()
        self.agreement.countersigner_name = "Pat Officer"
        self.agreement.countersigner_title = "Executive Director"
        self.agreement.countersigned_at = timezone.now()
        self.agreement.status = Agreement.Status.EXECUTED
        self.agreement.signature_method = Agreement.SignatureMethod.ACCOUNT
        self.agreement.save()

    def store_copy(self, kind, content):
        return SignedCopy.objects.create(
            agreement=self.agreement,
            kind=kind,
            filename=f"{kind}.pdf",
            content=content,
            uploaded_by=self.officer,
        )

    def test_signature_record_renders_counterparty_name_literally_for_all_methods(self):
        for method in Agreement.SignatureMethod.values:
            with self.subTest(method=method):
                self.agreement.signature_method = method
                markdown = documents.final_markdown(self.agreement)

                html, _ = documents.render_html(markdown)
                self.assertIn(self.agreement.counterparty_name, html)
                self.assertNotIn("<img", html)
                self.assertNotIn("<strong>LLC</strong>", html)

    def test_email_attaches_stored_executed_copy_without_rendering(self):
        self.store_copy(SignedCopy.Kind.CUSTOMER, b"%PDF-1.4 customer signature only")
        executed = b"%PDF-1.4 both external signatures and audit pages"
        self.store_copy(SignedCopy.Kind.EXECUTED, executed)

        with (
            patch.object(notifications, "final_markdown") as final_markdown,
            patch.object(notifications, "render_pdf") as render_pdf,
        ):
            notifications.send_executed_copy(self.agreement)

        final_markdown.assert_not_called()
        render_pdf.assert_not_called()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.agreement.signer_email])
        self.assertEqual(
            mail.outbox[0].attachments,
            [(f"psf-agreement-{self.agreement.reference}.pdf", executed, "application/pdf")],
        )

    def test_email_generates_executed_pdf_when_only_a_customer_copy_exists(self):
        customer_copy = b"%PDF-1.4 customer signature only"
        self.store_copy(SignedCopy.Kind.CUSTOMER, customer_copy)

        notifications.send_executed_copy(self.agreement)

        attachment = mail.outbox[-1].attachments[0]
        self.assertEqual(attachment[1], documents.render_pdf(documents.final_markdown(self.agreement)))
        self.assertNotEqual(attachment[1], customer_copy)
        self.assertEqual(attachment[2], "application/pdf")
