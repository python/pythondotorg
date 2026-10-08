from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.agreements import documents, workflow
from apps.agreements.auth import ADMINISTRATORS
from apps.agreements.documents import SIGNATURES
from apps.agreements.kinds import CustomContractKind
from apps.agreements.models import Agreement, AgreementRevision, CustomContract, SigningLink, Terms, TermsVersion

if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse

    from apps.users.models import User as UserModel

User = get_user_model()
PDF = b"%PDF-1.4 signed copy"


def make_officer(username: str = "pat") -> UserModel:
    officer = User.objects.create_user(username, f"{username}@example.org", "password")
    officer.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
    return officer


def make_terms(slug: str = "pycon-venue", markdown: str = "## 1. Scope\n\nThe venue hosts PyCon US.\n") -> Terms:
    terms = Terms.objects.create(slug=slug, title="PyCon Venue Terms")
    TermsVersion.objects.create(terms=terms, version="2026-01-01", markdown=markdown)
    return terms


def offer_contract(officer: UserModel, **overrides: Any) -> Agreement:
    fields = {
        "title": "PyCon US 2027 Venue Agreement",
        "counterparty_name": "Example Convention Center, LLC",
        "body_markdown": "## 1. Dates\n\nMay 12 to May 20, 2027.",
        "created_by": officer,
        **overrides,
    }
    contract = CustomContract.objects.create(**fields)
    return workflow.offer(CustomContractKind(), contract, user=officer)


def refresh(agreement: Agreement) -> Agreement:
    return Agreement.objects.get(pk=agreement.pk)


class OfferAndEditTests(TestCase):
    def setUp(self) -> None:
        self.officer = make_officer()
        self.client.force_login(self.officer)

    def test_offer_freezes_the_text_as_revision_one_and_cites_current_terms(self) -> None:
        terms = make_terms()
        agreement = offer_contract(self.officer, terms=terms)
        self.assertEqual(agreement.status, Agreement.Status.OFFERED)
        self.assertEqual(agreement.document_sha256, documents.sha256(agreement.document_markdown))
        self.assertEqual(list(agreement.terms_versions.all()), [terms.current_version])
        self.assertIn(cast("TermsVersion", terms.current_version).permanent_url, agreement.document_markdown)
        self.assertEqual(agreement.revisions.get().revision, 1)

        CustomContract.objects.filter(agreement=agreement).update(body_markdown="Changed after offer")
        self.assertNotIn("Changed after offer", refresh(agreement).document_markdown)

    def test_staff_edit_is_a_new_revision_and_keeps_the_old_text(self) -> None:
        agreement = offer_contract(self.officer)
        edited = agreement.document_markdown.replace("May 20", "May 21")
        response = self.client.post(
            reverse("agreements:edit", args=[agreement.pk]),
            {"markdown": edited, "note": "One more day", "base_sha256": agreement.document_sha256},
        )
        self.assertRedirects(response, agreement.get_absolute_url())
        agreement = refresh(agreement)
        self.assertEqual(agreement.revision, 2)
        self.assertIn("May 21", agreement.document_markdown)
        first = AgreementRevision.objects.get(agreement=agreement, revision=1)
        self.assertIn("May 20", first.markdown)
        self.assertEqual(agreement.revisions.get(revision=2).note, "One more day")

    def test_edit_from_a_stale_copy_is_refused(self) -> None:
        agreement = offer_contract(self.officer)
        stale = agreement.document_sha256
        workflow.edit(
            agreement,
            markdown=agreement.document_markdown + "\nFirst edit.",
            note="a",
            user=self.officer,
            base_sha256=stale,
        )
        with self.assertRaises(workflow.DocumentChangedError):
            workflow.edit(
                agreement,
                markdown=agreement.document_markdown + "\nLost edit.",
                note="b",
                user=self.officer,
                base_sha256=stale,
            )

    def test_edit_must_keep_the_signature_block(self) -> None:
        agreement = offer_contract(self.officer)
        response = self.client.post(
            reverse("agreements:edit", args=[agreement.pk]),
            {
                "markdown": agreement.document_markdown.replace(SIGNATURES, ""),
                "note": "oops",
                "base_sha256": agreement.document_sha256,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(refresh(agreement).revision, 1)

    def test_signed_agreements_cannot_be_edited(self) -> None:
        agreement = offer_contract(self.officer)
        workflow.record_signed_copy(
            agreement,
            workflow.Signature("Grace", "CTO", "grace@example.com", signed_on=timezone.localdate()),
            upload=workflow.Upload("s.pdf", PDF),
            user=self.officer,
            seen_sha256=agreement.document_sha256,
        )
        response = self.client.get(reverse("agreements:edit", args=[agreement.pk]))
        self.assertRedirects(response, agreement.get_absolute_url())

    def test_staff_written_text_cannot_embed_images(self) -> None:
        contract = CustomContract.objects.create(
            title="T", counterparty_name="C", body_markdown="![x](/etc/passwd)", created_by=self.officer
        )
        markdown = documents.preview_markdown(CustomContractKind().compose(contract), "C")
        for render in (documents.render_pdf, documents.render_docx):
            with self.subTest(render=render.__name__), self.assertRaises(RuntimeError):
                render(markdown)

    def test_withdrawing_returns_the_draft_for_editing(self) -> None:
        agreement = offer_contract(self.officer)
        contract = cast("CustomContract", agreement.subject)
        self.client.post(reverse("agreements:withdraw", args=[agreement.pk]))
        self.assertEqual(refresh(agreement).status, Agreement.Status.WITHDRAWN)
        contract.refresh_from_db()
        self.assertIsNone(contract.agreement)
        again = workflow.offer(CustomContractKind(), contract, user=self.officer)
        self.assertNotEqual(again.pk, agreement.pk)


class SigningLinkTests(TestCase):
    def setUp(self) -> None:
        self.officer = make_officer()
        self.agreement = offer_contract(self.officer)

    def send_link(self) -> str:
        self.client.force_login(self.officer)
        self.client.post(
            reverse("agreements:send_link", args=[self.agreement.pk]),
            {"name": "Grace Hopper", "email": "grace@example.com"},
        )
        self.client.logout()
        return cast(
            "re.Match[str]", re.search(r"/agreements/sign/([^/\s]+)/", cast("str", mail.outbox[-1].body))
        ).group(1)

    def sign(self, token: str, **overrides: Any) -> _MonkeyPatchedWSGIResponse:
        data = {
            "signer_name": "Grace Hopper",
            "signer_title": "General Manager",
            "accept": "on",
            "document_sha256": refresh(self.agreement).document_sha256,
            **overrides,
        }
        return self.client.post(reverse("agreements:sign_link", args=[token]), data)

    def test_emailed_link_signs_as_the_address_it_was_sent_to(self) -> None:
        token = self.send_link()
        self.assertEqual(mail.outbox[-1].to, ["grace@example.com"])
        self.assertFalse(SigningLink.objects.filter(token_sha256=token).exists())

        page = self.client.get(reverse("agreements:sign_link", args=[token]))
        self.assertContains(page, "Example Convention Center")

        self.sign(token, signer_name="Grace Hopper")
        agreement = refresh(self.agreement)
        self.assertEqual(agreement.status, Agreement.Status.SIGNED)
        self.assertEqual(agreement.signature_method, Agreement.SignatureMethod.LINK)
        self.assertEqual(agreement.signer_email, "grace@example.com")

    def test_link_form_passes_csrf_checks_as_a_browser_sends_it(self) -> None:
        token = self.send_link()
        browser = Client(enforce_csrf_checks=True)
        url = reverse("agreements:sign_link", args=[token])
        page = browser.get(url)
        # Browsers send "Origin: null" on a form POST from a page with "no-referrer".
        origin = "null" if page["Referrer-Policy"] == "no-referrer" else "http://testserver"
        browser.post(
            url,
            {
                "csrfmiddlewaretoken": page.context["csrf_token"],
                "signer_name": "Grace Hopper",
                "signer_title": "General Manager",
                "accept": "on",
                "document_sha256": self.agreement.document_sha256,
            },
            HTTP_ORIGIN=origin,
        )
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.SIGNED)

    def test_link_works_once(self) -> None:
        token = self.send_link()
        self.sign(token)
        self.assertEqual(self.client.get(reverse("agreements:sign_link", args=[token])).status_code, 410)

    def test_expired_link_does_not_work(self) -> None:
        token = self.send_link()
        SigningLink.objects.update(expires_at=timezone.now() - datetime.timedelta(minutes=1))
        self.assertEqual(self.sign(token).status_code, 410)
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.OFFERED)

    def test_signature_is_refused_if_the_text_changed_after_the_signer_opened_it(self) -> None:
        token = self.send_link()
        seen = self.agreement.document_sha256
        workflow.edit(
            self.agreement,
            markdown=self.agreement.document_markdown + "\nNew clause.",
            note="edit",
            user=self.officer,
            base_sha256=seen,
        )
        self.sign(token, document_sha256=seen)
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.OFFERED)
        self.sign(token)
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.SIGNED)

    def test_withdrawn_offer_disables_its_links(self) -> None:
        token = self.send_link()
        workflow.withdraw(self.agreement, user=self.officer)
        self.assertEqual(self.client.get(reverse("agreements:sign_link", args=[token])).status_code, 410)


class SignedCopyAndCountersignTests(TestCase):
    def setUp(self) -> None:
        self.officer = make_officer()
        self.other = User.objects.create_user("eve", "eve@example.com", "password")
        self.agreement = offer_contract(self.officer)
        self.client.force_login(self.officer)

    def record(self, content: bytes = PDF, **overrides: Any) -> _MonkeyPatchedWSGIResponse:
        data = {
            "signed_copy": SimpleUploadedFile("signed.pdf", content, content_type="application/pdf"),
            "signer_name": "Grace Hopper",
            "signer_title": "CTO",
            "signer_email": "grace@example.com",
            "signed_on": "2026-09-01",
            "matches": "on",
            "document_sha256": self.agreement.document_sha256,
            **overrides,
        }
        return self.client.post(reverse("agreements:record_copy", args=[self.agreement.pk]), data)

    def test_signed_copy_is_kept_and_cited_in_the_record(self) -> None:
        self.record()
        agreement = refresh(self.agreement)
        self.assertEqual(agreement.signature_method, Agreement.SignatureMethod.OFFLINE)
        self.assertEqual(cast("datetime.datetime", agreement.signed_at).date(), datetime.date(2026, 9, 1))
        text = documents.final_markdown(agreement)
        self.assertIn("Signed copy on file", text)

        download = reverse("agreements:copy_download", args=[agreement.pk, "customer"])
        self.assertEqual(self.client.get(download).content, PDF)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(download).status_code, 404)

    def test_only_pdfs_are_accepted(self) -> None:
        self.assertEqual(self.record(content=b"<html></html>").status_code, 400)
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.OFFERED)

    def test_only_the_psf_countersigns_and_the_signatory_gets_the_executed_copy(self) -> None:
        self.record()
        url = reverse("agreements:countersign", args=[self.agreement.pk])
        payload = {"name": "Pat Officer", "title": "Executive Director", "accept": "on"}
        self.client.force_login(self.other)
        self.client.post(url, payload)
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.SIGNED)

        self.client.force_login(self.officer)
        self.client.post(url, payload)
        self.assertEqual(refresh(self.agreement).status, Agreement.Status.EXECUTED)
        email = mail.outbox[-1]
        self.assertEqual(email.to, ["grace@example.com"])
        self.assertTrue(email.attachments[0][1].startswith(b"%PDF"))

    def test_agreements_are_private(self) -> None:
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.agreement.get_absolute_url()).status_code, 404)


class TermsPublishingTests(TestCase):
    def setUp(self) -> None:
        self.officer = make_officer()
        self.client.force_login(self.officer)
        self.terms = make_terms()
        self.url = reverse("agreements:terms_edit", args=[self.terms.slug])

    def publish(
        self, markdown: str, version: str = "2026-06-01", notes: str = "Longer load-in window"
    ) -> _MonkeyPatchedWSGIResponse:
        return self.client.post(
            self.url, {"markdown": markdown, "version": version, "notes": notes, "action": "publish"}
        )

    def test_new_version_applies_only_to_documents_offered_afterwards(self) -> None:
        before = offer_contract(self.officer, terms=self.terms)
        self.publish("## 1. Scope\n\nThe venue hosts PyCon US and its sprints.\n")
        self.terms = Terms.objects.get(pk=self.terms.pk)
        after = offer_contract(self.officer, terms=self.terms)

        self.assertEqual(before.terms_versions.get().version, "2026-01-01")
        self.assertEqual(after.terms_versions.get().version, "2026-06-01")
        old = self.client.get(reverse("agreements:terms_version", args=[self.terms.slug, "2026-01-01"]))
        self.assertContains(old, "earlier version")
        self.assertNotContains(old, "sprints")

    def test_drafts_stay_private_until_published(self) -> None:
        self.client.post(self.url, {"markdown": "## 1. Scope\n\nSecret draft.\n", "action": "save"})
        self.assertEqual(Terms.objects.get(pk=self.terms.pk).draft_markdown, "## 1. Scope\n\nSecret draft.\n")
        self.client.logout()
        response = self.client.get(self.terms.get_absolute_url())
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(b"Secret draft", response.content)

    def test_version_labels_are_never_reused_and_versions_never_change(self) -> None:
        response = self.publish("Different text\n", version="2026-01-01")
        self.assertEqual(response.status_code, 400)
        version = cast("TermsVersion", self.terms.current_version)
        version.markdown = "Rewritten"
        with self.assertRaises(ValueError):
            version.save()


class TermsAccessTests(TestCase):
    def setUp(self) -> None:
        self.officer = make_officer()
        self.customer = User.objects.create_user("customer", "customer@example.org", "password")
        self.stranger = User.objects.create_user("stranger", "stranger@example.org", "password")
        self.terms = make_terms()
        self.version = cast("TermsVersion", self.terms.current_version)
        self.agreement = offer_contract(self.officer, terms=self.terms, counterparty_account=self.customer)

    def test_private_terms_only_expose_versions_cited_to_the_counterparty(self) -> None:
        newer = TermsVersion.objects.create(
            terms=self.terms, version="2026-08-01", markdown="## New confidential terms\n"
        )
        url = self.version.get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.customer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.client.get(newer.get_absolute_url()).status_code, 404)
        download = reverse("agreements:terms_version_download", args=[self.terms.slug, self.version.version, "docx"])
        self.assertEqual(self.client.get(download).status_code, 200)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(download).status_code, 404)

    def test_publication_is_independent_of_version_creation(self) -> None:
        url = self.version.get_absolute_url()
        self.assertEqual(self.client.get(url).status_code, 404)
        self.terms.is_public = True
        self.terms.save(update_fields=["is_public"])
        self.assertContains(self.client.get(url), self.terms.title)

    def test_signing_link_grants_only_its_cited_terms_until_consumed(self) -> None:
        _, token = workflow.create_signing_link(
            self.agreement, name="Customer", email=self.customer.email, user=self.officer
        )
        url = reverse("agreements:sign_link_terms", args=[token, self.version.pk])
        self.assertContains(self.client.get(reverse("agreements:sign_link", args=[token])), url)
        self.assertContains(self.client.get(url), self.terms.title)
        unrelated = cast("TermsVersion", make_terms(slug="another-contract").current_version)
        self.assertEqual(
            self.client.get(reverse("agreements:sign_link_terms", args=[token, unrelated.pk])).status_code, 404
        )
        download = reverse("agreements:sign_link_terms_download", args=[token, self.version.pk, "docx"])
        self.assertEqual(self.client.get(download).status_code, 200)
        workflow.sign_with_link(
            cast("SigningLink", workflow.find_link(token)),
            workflow.Signature("Customer", "Director", self.customer.email),
            seen_sha256=self.agreement.document_sha256,
        )
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.get(download).status_code, 404)

    def test_preview_does_not_publish_terms(self) -> None:
        self.client.force_login(self.officer)
        self.client.post(
            reverse("agreements:terms_edit", args=[self.terms.slug]),
            {"markdown": "## Preview\n", "preview": "1", "is_public": "on"},
        )
        self.terms.refresh_from_db()
        self.assertFalse(self.terms.is_public)
