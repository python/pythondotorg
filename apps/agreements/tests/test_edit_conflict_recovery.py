from unittest.mock import patch

from django.contrib.messages import ERROR, get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape

from apps.agreements import documents, workflow
from apps.agreements.models import Agreement
from apps.agreements.tests.test_agreements import make_officer, offer_contract
from apps.agreements.views.helpers import _agreement_or_404


class EditConflictRecoveryTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.client.force_login(self.officer)
        self.agreement = offer_contract(self.officer)
        self.url = reverse("agreements:edit", args=[self.agreement.pk])
        opened = self.client.get(self.url)
        self.base_sha256 = opened.context["form"]["base_sha256"].value()
        self.current = self.agreement.document_markdown.replace("May 20", "May 21")
        self.proposed = self.agreement.document_markdown + "\nProposed <replacement> & additions.\n"
        self.note = "Preserve my <note> & reason"

    def save_concurrent_edit(self, markdown):
        self.agreement = workflow.edit(
            self.agreement,
            markdown=markdown,
            note="Concurrent edit",
            user=self.officer,
            base_sha256=self.agreement.document_sha256,
        )

    def post_edit(self, markdown, base_sha256):
        return self.client.post(
            self.url,
            {"markdown": markdown, "note": self.note, "base_sha256": base_sha256, "save": ""},
        )

    def history(self):
        return list(self.agreement.revisions.values())

    def conflict_response(self):
        self.save_concurrent_edit(self.current)
        history = self.history()
        response = self.post_edit(self.proposed, self.base_sha256)
        self.assertEqual(response.status_code, 409)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.document_markdown, self.current)
        self.assertEqual(self.agreement.document_sha256, documents.sha256(self.current))
        self.assertEqual(self.agreement.revision, 2)
        self.assertEqual(self.history(), history)
        return response

    def test_reviewed_replacement_can_be_saved_without_losing_submitted_work(self):
        response = self.conflict_response()
        form = response.context["form"]
        self.assertEqual(form["markdown"].value(), self.proposed)
        self.assertEqual(form["note"].value(), self.note)
        self.assertEqual(form["base_sha256"].value(), self.agreement.document_sha256)
        self.assertContains(response, escape(self.current), status_code=409)
        self.assertContains(response, escape(self.proposed), status_code=409)
        self.assertContains(response, escape(self.note), status_code=409)
        self.assertContains(response, "-May 12 to May 21, 2027.", status_code=409)
        self.assertContains(response, "+May 12 to May 20, 2027.", status_code=409)

        merged = self.proposed.replace("May 20", "May 21")
        response = self.post_edit(merged, form["base_sha256"].value())
        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.revision, 3)
        self.assertEqual(self.agreement.document_markdown, merged)
        self.assertEqual(self.agreement.document_sha256, documents.sha256(merged))
        revision = self.agreement.revisions.get(revision=3)
        self.assertEqual(revision.markdown, merged)
        self.assertEqual(revision.note, self.note)
        self.assertEqual(self.agreement.revisions.get(revision=2).markdown, self.current)
        self.assertEqual(self.agreement.revisions.count(), 3)

    def test_another_edit_after_review_conflicts_again(self):
        response = self.conflict_response()
        reviewed_sha256 = response.context["form"]["base_sha256"].value()
        newest = self.current + "\nAnother concurrent change.\n"
        self.save_concurrent_edit(newest)
        history = self.history()
        merged = self.proposed.replace("May 20", "May 21")

        response = self.post_edit(merged, reviewed_sha256)

        self.assertEqual(response.status_code, 409)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.document_markdown, newest)
        self.assertEqual(self.agreement.revision, 3)
        self.assertEqual(self.history(), history)
        self.assertEqual(response.context["form"]["markdown"].value(), merged)
        self.assertEqual(response.context["form"]["note"].value(), self.note)
        self.assertEqual(response.context["form"]["base_sha256"].value(), self.agreement.document_sha256)
        self.assertContains(response, escape(newest), status_code=409)

    def test_conflict_reloads_changes_committed_after_view_loaded_agreement(self):
        def load_then_edit(request, pk):
            loaded = _agreement_or_404(request, pk)
            self.save_concurrent_edit(self.current)
            return loaded

        with patch("apps.agreements.views.agreements._agreement_or_404", side_effect=load_then_edit):
            response = self.post_edit(self.proposed, self.base_sha256)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.context["agreement"].revision, 2)
        self.assertEqual(response.context["form"]["base_sha256"].value(), self.agreement.document_sha256)
        self.assertContains(response, escape(self.current), status_code=409)
        self.assertEqual(self.agreement.revisions.count(), 2)

    def sign(self):
        workflow.sign(
            self.agreement,
            workflow.Signature("Grace Hopper", "CTO", "grace@example.com"),
            seen_sha256=self.agreement.document_sha256,
        )

    def assert_signed_document_unchanged(self, history):
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.SIGNED)
        self.assertEqual(self.agreement.document_markdown, self.current)
        self.assertEqual(self.agreement.document_sha256, documents.sha256(self.current))
        self.assertEqual(self.agreement.revision, 2)
        self.assertEqual(self.history(), history)

    def test_signing_after_review_prevents_replacement(self):
        response = self.conflict_response()
        reviewed_sha256 = response.context["form"]["base_sha256"].value()
        history = self.history()
        self.sign()

        response = self.post_edit(self.proposed, reviewed_sha256)

        self.assertRedirects(response, self.agreement.get_absolute_url())
        self.assert_signed_document_unchanged(history)

    def test_signing_after_view_loaded_agreement_prevents_replacement(self):
        response = self.conflict_response()
        reviewed_sha256 = response.context["form"]["base_sha256"].value()
        history = self.history()

        def load_then_sign(request, pk):
            loaded = _agreement_or_404(request, pk)
            self.sign()
            return loaded

        with patch("apps.agreements.views.agreements._agreement_or_404", side_effect=load_then_sign):
            response = self.post_edit(self.proposed, reviewed_sha256)

        self.assertIn(ERROR, [message.level for message in get_messages(response.wsgi_request)])
        self.assert_signed_document_unchanged(history)
