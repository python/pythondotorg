"""Order behavior against an entirely fictional, database-configured program."""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlsplit
from zipfile import ZipFile

from defusedxml.ElementTree import fromstring
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.agreements import documents as agreement_documents
from apps.agreements import workflow
from apps.agreements.auth import ADMINISTRATORS
from apps.agreements.models import Agreement, Order, OrderLine, Program, Terms, TermsVersion
from apps.agreements.orders import documents
from apps.agreements.registry import get_kind
from apps.agreements.tests.catalog_data import make_program
from apps.agreements.tests.test_agreements import PrivateStorageTestCase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.http import HttpResponseRedirect
    from django.test.client import _MonkeyPatchedWSGIResponse

    from apps.users.models import User as UserModel

User = get_user_model()
STUDIO: dict[str, Any] = {"tier": "plus"}
WORKSHOP: dict[str, Any] = {"tier": "basic", "addons": {"kit": {}}}


def make_order(
    user: UserModel,
    agreements: dict[str, dict[str, Any]] | None = None,
    *,
    program: Program,
    **overrides: Any,
) -> Order:
    order = Order.objects.create(
        **{
            "program": program,
            "created_by": user,
            "customer_account": user,
            "legal_name": "Example Workshops, Inc.",
            "jurisdiction": "Delaware",
            "entity_type": "corporation",
            "address": "100 Example Street\nPortland, OR",
            "covered_entities": "example-workspace",
            "authorized_contacts": [{"name": "Ada Byron", "email": "ada@example.com"}],
            "billing_contact_name": "Accounts Payable",
            "billing_contact_email": "ap@example.com",
            **overrides,
        }
    )
    for slug, selections in (agreements or {"studio": STUDIO}).items():
        line_selections = dict(selections)
        if "services" not in line_selections:
            line_selections["services"] = [
                service.key for service in order.catalog.agreements[slug].services_at(line_selections["tier"])
            ]
        OrderLine.objects.create(order=order, agreement=slug, **line_selections)
    return order


def make_officer(username: str = "pat") -> UserModel:
    officer = User.objects.create_user(username, f"{username}@example.org", "password")
    officer.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
    return officer


def reload(order: Order) -> Order:
    return Order.objects.select_related("agreement", "program").get(pk=order.pk)


def payload(agreements: Iterable[str] = ("studio", "workshop"), **overrides: Any) -> dict[str, Any]:
    return {
        "agreements": list(agreements),
        "legal_name": "Example Workshops, Inc.",
        "jurisdiction": "Delaware",
        "entity_type": "corporation",
        "address": "100 Example Street",
        "covered_entities": "example-workspace",
        "discount": "none",
        "contact_1_name": "Ada Byron",
        "contact_1_email": "ada@example.com",
        "billing_contact_name": "AP",
        "billing_contact_email": "ap@example.com",
        "studio-tier": "basic",
        "studio-services": ["access"],
        "workshop-tier": "max",
        "workshop-services": ["materials", "planning"],
        **overrides,
    }


class OrderFormDocumentTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("ada", "ada@example.com", "password")
        self.program = make_program()

    def test_recurring_and_one_time_fees_are_separate_without_repricing_snapshots(self) -> None:
        order = make_order(
            self.user,
            {
                "studio": {"tier": "basic"},
                "workshop": {"tier": "max", "addons": {"kit": {}, "sessions": {"hours": 2}}},
            },
            program=self.program,
            discount="prepaid",
        )
        self.client.force_login(self.user)
        self.assertEqual(order.term_total_display, "$22,656")
        markdown = documents.compose_order_form_markdown(order)
        self.assertIn("**Total annual fees** | **$7,527**", markdown)
        self.assertIn("Total one-time fees | $75", markdown)
        self.assertNotIn("**Total annual fees** | **$7,602**", markdown)
        detail = self.client.get(order.get_absolute_url())
        self.assertContains(detail, "$6,471 a year")
        self.assertContains(detail, "$75 one-time")
        listing = self.client.get(reverse("agreements:order_list"))
        self.assertContains(listing, "$7,527 a year")
        self.assertContains(listing, "$75 one-time")

        agreement = workflow.offer(get_kind("order"), order, user=self.user)
        frozen = reload(order)
        snapshots = list(frozen.agreements.values_list("pricing", flat=True))
        original = documents.order_form_markdown(frozen)
        definition = deepcopy(self.program.definition)
        definition["agreements"][0]["tiers"][0]["annual_fee"] = "9999"
        Program.objects.filter(pk=self.program.pk).update(definition=definition)
        frozen = reload(order)
        self.assertEqual(frozen.fee_totals, {"annual": 7527, "one_time": 75})
        self.assertEqual(documents.order_form_markdown(reload(order)), original)
        self.assertEqual(list(frozen.agreements.values_list("pricing", flat=True)), snapshots)
        self.assertEqual(cast("Agreement", reload(order).agreement).document_markdown, agreement.document_markdown)

    def test_order_reference_stays_consistent_across_offers_and_withdrawal(self) -> None:
        order = make_order(self.user, program=self.program)
        agreement = workflow.offer(get_kind("order"), order, user=self.user)
        self.assertEqual(agreement.reference, order.reference)
        self.client.force_login(self.user)
        self.assertContains(self.client.get(agreement.get_absolute_url()), f"<code>{order.reference}</code>")
        workflow.withdraw(agreement, user=self.user)
        agreement.refresh_from_db()
        self.assertEqual(agreement.reference, order.reference)
        replacement = workflow.offer(get_kind("order"), reload(order), user=self.user)
        self.assertNotEqual(agreement.pk, replacement.pk)
        self.assertEqual(replacement.reference, order.reference)

    def test_legacy_fingerprints_are_hidden_without_changing_the_signed_document(self) -> None:
        order = make_order(self.user, {"studio": STUDIO, "workshop": WORKSHOP}, program=self.program)
        agreement = workflow.offer(get_kind("order"), order, user=self.user)
        versions = list(agreement.terms_versions.all())
        legacy = agreement.document_markdown
        fingerprints = []
        for index, version in enumerate(versions):
            digest = version.sha256
            fingerprint = (
                f"`{digest}`" if index else " ".join(digest[offset : offset + 16] for offset in range(0, 64, 16))
            )
            fingerprints.append(fingerprint.strip("`"))
            citation = f"published at <{version.permanent_url}>"
            legacy = legacy.replace(f"{citation}.", f"{citation}, SHA-256 {fingerprint}.")
        # This is substantive contract text, not generated terms-identification metadata.
        legacy += "\nThe service must use SHA-256 to verify uploaded files.\n"
        workflow.edit(
            agreement, markdown=legacy, note="Legacy document", user=self.user, base_sha256=agreement.document_sha256
        )
        agreement.refresh_from_db()
        stored_hash = agreement.document_sha256
        _, token = workflow.create_signing_link(agreement, name="Ada", email=self.user.email, user=self.user)
        link_page = self.client.get(reverse("agreements:sign_link", args=[token]))
        self.assertNotIn(fingerprints[0], link_page.context["html"])
        workflow.sign(agreement, workflow.Signature("Ada", "Director", self.user.email), seen_sha256=stored_hash)
        self.client.force_login(self.user)
        for url in (agreement.get_absolute_url(), order.get_absolute_url()):
            with self.subTest(url=url):
                page = self.client.get(url)
                for fingerprint in fingerprints:
                    self.assertNotIn(fingerprint, page.context["html"])
                self.assertContains(page, "use SHA-256 to verify uploaded files")
                for version in versions:
                    self.assertContains(page, version.permanent_url)
        download = self.client.get(reverse("agreements:document", args=[agreement.pk, "docx"]))
        with ZipFile(BytesIO(download.content)) as archive:
            xml = fromstring(archive.read("word/document.xml"))
        downloaded_text = " ".join("".join(xml.itertext()).split())
        for fingerprint in fingerprints:
            self.assertIn(fingerprint, downloaded_text)
        agreement.refresh_from_db()
        self.assertEqual(agreement.document_markdown, legacy)
        self.assertEqual(agreement.document_sha256, stored_hash)
        self.assertEqual(agreement.revisions.get(revision=agreement.revision).markdown, legacy)

    def test_customer_input_renders_as_literal_text(self) -> None:
        order = make_order(
            self.user,
            program=self.program,
            legal_name="<script>alert(1)</script> [x](javascript:alert(1)) *bold* | pipe",
            covered_entities="\\input{/etc/passwd}\n$x$",
        )
        html, _ = agreement_documents.render_html(documents.order_form_markdown(order))
        self.assertNotIn("<script>", html)
        self.assertNotIn('href="javascript', html)
        self.assertNotIn("<em>bold</em>", html)
        self.assertIn("\\input{/etc/passwd}", html)
        self.assertIn("$x$", html)
        self.assertIn("*BOLD* | PIPE</strong></th>", html)

    def test_pdf_renders_names_outside_pdflatex_coverage(self) -> None:
        order = make_order(self.user, program=self.program, legal_name="株式会社テスト − Ωmega")  # noqa: RUF001
        pdf = agreement_documents.render_pdf(documents.order_form_markdown(order))
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_order_form_cites_terms_instead_of_repeating_them(self) -> None:
        order = make_order(self.user, {"studio": STUDIO, "workshop": WORKSHOP}, program=self.program)
        text = documents.order_form_markdown(order)
        for line in order.agreement_list:
            version = cast("TermsVersion", line.cited_terms)
            with self.subTest(agreement=line.agreement):
                self.assertIn(f"<{version.permanent_url}>", text)
                self.assertNotIn(version.markdown.strip(), text)
                self.assertEqual(self.client.get(urlsplit(version.permanent_url).path).status_code, 200)

    def test_order_form_lists_only_services_the_tier_includes(self) -> None:
        for tier, planning in (("basic", False), ("plus", True)):
            with self.subTest(tier=tier):
                order = make_order(self.user, {"studio": {"tier": tier}}, program=self.program)
                text = documents.order_form_markdown(order)
                self.assertIn("Studio access", text)
                self.assertEqual("Studio planning" in text, planning)

    def test_document_uses_configured_copy_and_all_parameter_kinds(self) -> None:
        order = make_order(
            self.user,
            {
                "workshop": {
                    "tier": "basic",
                    "addons": {
                        "labels": {"names": ["East room", "West room"]},
                        "reports": {"mode": "single", "copies": 3},
                        "schedule": {"window": "Weekends"},
                    },
                }
            },
            program=self.program,
        )
        html, _ = agreement_documents.render_html(documents.order_form_markdown(order))
        text = " ".join(html.split())
        for value in ("East room; West room", "Individual", "Weekends", "$57"):
            self.assertIn(value, text)


class OnlineSigningTests(TestCase):
    def setUp(self) -> None:
        self.customer = User.objects.create_user("ada", "ada@example.com", "password")
        self.other = User.objects.create_user("eve", "eve@example.com", "password")
        self.officer = make_officer()
        self.program = make_program()
        self.order = make_order(self.customer, {"studio": STUDIO, "workshop": WORKSHOP}, program=self.program)

    def preview_sha256(self) -> str:
        return agreement_documents.sha256(documents.compose_order_form_markdown(reload(self.order)))

    def sign(self, **data: Any) -> _MonkeyPatchedWSGIResponse:
        self.client.force_login(self.customer)
        return self.client.post(
            reverse("agreements:order_sign", args=[self.order.pk]),
            {
                "signer_name": "Ada Byron",
                "signer_title": "General Counsel",
                "accept": "on",
                "document_sha256": self.preview_sha256(),
                **data,
            },
        )

    def countersign(self, user: UserModel) -> _MonkeyPatchedWSGIResponse:
        self.client.force_login(user)
        return self.client.post(
            reverse("agreements:countersign", args=[cast("Agreement", reload(self.order).agreement).pk]),
            {
                "name": "Pat Officer",
                "title": "Executive Director",
                "accept": "on",
            },
        )

    def test_signing_freezes_document_catalog_terms_and_fees(self) -> None:
        OrderLine.objects.filter(order=self.order, agreement="studio").update(services=["planning"])
        self.sign()
        order = reload(self.order)
        original = documents.order_form_markdown(order)
        self.assertIn("Studio planning", original)
        self.assertNotIn("Studio access", original)
        self.assertEqual(order.status, Agreement.Status.SIGNED)
        self.assertEqual(cast("Agreement", order.agreement).signature_method, Agreement.SignatureMethod.ACCOUNT)
        self.assertEqual(cast("Agreement", order.agreement).signer_email, "ada@example.com")
        self.assertEqual(cast("Agreement", order.agreement).terms_versions.count(), 2)
        old_total = order.fee_totals
        definition = deepcopy(self.program.definition)
        definition["agreements"][0]["title"] = "Changed service"
        definition["agreements"][0]["tiers"][1]["annual_fee"] = "9999"
        definition["agreements"][0]["services"] = []
        definition["order_title"] = "Changed order title"
        Program.objects.filter(pk=self.program.pk).update(title="Changed program", definition=definition)
        Order.objects.filter(pk=order.pk).update(legal_name="Changed After Signing")
        frozen = reload(order)
        self.assertEqual(documents.order_form_markdown(frozen), original)
        self.assertEqual(frozen.fee_totals, old_total)
        self.assertEqual(frozen.program_title, "Example Services")
        self.assertEqual(frozen.agreement_list[0].agreement_obj.title, "Example Studio Services")
        self.assertEqual(frozen.agreement_list[0].services, ["planning"])
        self.assertEqual([service.name for service in frozen.agreement_list[0].selected_services], ["Studio planning"])

    def test_signing_refuses_a_changed_preview_without_leaving_an_offer(self) -> None:
        for changes in ({"tier": "max"}, {"services": ["planning"]}):
            with self.subTest(changes=changes):
                seen = self.preview_sha256()
                OrderLine.objects.filter(order=self.order, agreement="studio").update(**changes)
                self.sign(document_sha256=seen)
                self.assertIsNone(reload(self.order).agreement)

    def test_signing_requires_acceptance(self) -> None:
        self.assertEqual(self.sign(accept="").status_code, 400)
        self.assertIsNone(reload(self.order).agreement)

    def test_signed_orders_cannot_be_edited(self) -> None:
        self.sign()
        response = self.client.post(reverse("agreements:order_edit", args=[self.order.pk]), {"legal_name": "X"})
        self.assertRedirects(response, self.order.get_absolute_url())
        self.assertEqual(reload(self.order).legal_name, "Example Workshops, Inc.")

    def test_orders_and_documents_are_private(self) -> None:
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.order.get_absolute_url()).status_code, 404)
        self.assertEqual(
            self.client.get(reverse("agreements:order_document", args=[self.order.pk, "pdf"])).status_code, 404
        )

    def test_only_the_psf_countersigns(self) -> None:
        self.sign()
        self.countersign(self.customer)
        self.assertEqual(reload(self.order).status, Agreement.Status.SIGNED)
        self.countersign(self.officer)
        order = reload(self.order)
        self.assertEqual(order.status, Agreement.Status.EXECUTED)
        text = documents.order_form_markdown(order)
        self.assertIn("/s/ Pat Officer", text)
        self.assertIn("/s/ Ada Byron", text)


class StaffHandlingTests(PrivateStorageTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.officer = make_officer()
        self.customer = User.objects.create_user("ada", "ada@example.com", "password")
        self.program = make_program()
        self.client.force_login(self.officer)

    def test_staff_queue_requires_login_and_agreement_group(self) -> None:
        url = reverse("agreements:staff_orders")
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("next=" + url, cast("HttpResponseRedirect", response).url)

    def post(self, **overrides: Any) -> _MonkeyPatchedWSGIResponse:
        return self.client.post(
            reverse("agreements:order_create", args=[self.program.slug]), payload(["studio"], **overrides)
        )

    def test_staff_order_assigned_to_an_account_can_be_signed_by_that_customer(self) -> None:
        self.post(customer_account_email="ADA@example.com", **{"studio-special_terms": "Net 45 payment."})
        order = Order.objects.get()
        self.assertEqual(order.created_by, self.officer)
        self.assertEqual(order.customer_account, self.customer)
        self.assertIn("Net 45 payment", documents.order_form_markdown(order))
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(reverse("agreements:order_list")), order.legal_name)
        seen = agreement_documents.sha256(documents.compose_order_form_markdown(order))
        self.client.post(
            reverse("agreements:order_sign", args=[order.pk]),
            {
                "signer_name": "Ada Byron",
                "signer_title": "CEO",
                "accept": "on",
                "document_sha256": seen,
            },
        )
        self.assertEqual(reload(order).status, Agreement.Status.SIGNED)

    def test_unknown_customer_account_is_rejected(self) -> None:
        self.assertEqual(self.post(customer_account_email="nobody@example.com").status_code, 200)
        self.assertFalse(Order.objects.exists())

    def test_order_without_an_account_can_be_signed_offline(self) -> None:
        self.post()
        order = Order.objects.get()
        self.assertIsNone(order.customer_account)
        self.client.post(reverse("agreements:order_offer", args=[order.pk]))
        offered = reload(order)
        self.client.post(
            reverse("agreements:record_copy", args=[cast("Agreement", offered.agreement).pk]),
            {
                "signed_copy": SimpleUploadedFile(
                    "signed.pdf", b"%PDF-1.4 signed copy", content_type="application/pdf"
                ),
                "signer_name": "Ada Byron",
                "signer_title": "CEO",
                "signer_email": "ada@example.com",
                "signed_on": timezone.localdate(),
                "matches": "on",
                "document_sha256": cast("Agreement", offered.agreement).document_sha256,
            },
        )
        signed = reload(order)
        self.assertEqual(signed.status, Agreement.Status.SIGNED)
        self.assertEqual(cast("Agreement", signed.agreement).signature_method, Agreement.SignatureMethod.OFFLINE)
        self.assertEqual(cast("Agreement", signed.agreement).signer_email, "ada@example.com")

    def test_staff_document_edit_is_the_version_the_customer_signs(self) -> None:
        order = make_order(self.customer, program=self.program)
        agreement = workflow.offer(get_kind("order"), order, user=self.officer)
        edited = agreement.document_markdown.replace(
            "## Signatures", "## Additional terms\n\nPayment is due within forty-five (45) days.\n\n## Signatures"
        )
        self.client.post(
            reverse("agreements:edit", args=[agreement.pk]),
            {
                "markdown": edited,
                "note": "Net 45, agreed with customer",
                "base_sha256": agreement.document_sha256,
            },
        )
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(order.get_absolute_url()), "forty-five (45) days")
        agreement.refresh_from_db()
        self.client.post(
            reverse("agreements:sign", args=[agreement.pk]),
            {
                "signer_name": "Ada",
                "signer_title": "CEO",
                "accept": "on",
                "document_sha256": agreement.document_sha256,
            },
        )
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, Agreement.Status.SIGNED)
        self.assertIn("forty-five (45) days", agreement.document_markdown)

    def test_withdrawing_reopens_the_order_at_current_prices(self) -> None:
        order = make_order(self.customer, {"studio": {"tier": "plus", "services": ["access"]}}, program=self.program)
        agreement = workflow.offer(get_kind("order"), order, user=self.officer)
        definition = deepcopy(self.program.definition)
        definition["agreements"][0]["tiers"][1]["annual_fee"] = "2600"
        Program.objects.filter(pk=self.program.pk).update(definition=definition)
        self.assertEqual(reload(order).fee_totals["annual"], 2400)
        self.client.post(reverse("agreements:withdraw", args=[agreement.pk]))
        reopened = reload(order)
        self.assertTrue(reopened.is_editable)
        self.assertEqual(reopened.fee_totals["annual"], 2600)
        self.assertEqual(reopened.agreements.get().services, ["access"])
        text = documents.order_form_markdown(reopened)
        self.assertIn("Studio access", text)
        self.assertNotIn("Studio planning", text)

    def test_published_terms_apply_only_to_orders_offered_afterwards(self) -> None:
        terms = Terms.objects.get(slug="studio-terms")
        before = make_order(self.customer, program=self.program)
        workflow.offer(get_kind("order"), before, user=self.officer)
        TermsVersion.objects.create(
            terms=terms, version="example-2", markdown=cast("TermsVersion", terms.current_version).markdown + "\nNew."
        )
        later = make_order(self.customer, program=self.program)
        self.assertIn("/example-2/", documents.order_form_markdown(later))
        self.assertIn("/example-1/", documents.order_form_markdown(reload(before)))


class OrderBuilderTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("ada", "ada@example.com", "password")
        self.program = make_program()
        self.client.force_login(self.user)
        self.url = reverse("agreements:order_create", args=[self.program.slug])

    def test_one_order_combines_agreements_in_catalog_order(self) -> None:
        self.client.post(self.url, payload(["workshop", "studio"]))
        order = Order.objects.get()
        self.assertEqual([line.agreement for line in order.agreement_list], ["studio", "workshop"])
        self.assertEqual(order.agreements.get(agreement="workshop").tier, "max")
        self.assertEqual(order.customer_account, self.user)

    def test_selected_services_persist_and_render_without_unselected_scope(self) -> None:
        response = self.client.post(
            self.url,
            payload(["studio"], **{"studio-tier": "plus", "studio-services": ["planning"]}),
        )
        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.agreements.get().services, ["planning"])
        self.assertContains(self.client.get(order.get_absolute_url()), "Studio planning")
        self.assertNotContains(self.client.get(order.get_absolute_url()), "Studio access")
        text = documents.order_form_markdown(order)
        self.assertIn("Studio planning", text)
        self.assertNotIn("Studio access", text)

        response = self.client.post(
            reverse("agreements:order_edit", args=[order.pk]),
            payload(["studio"], **{"studio-tier": "plus", "studio-services": ["access"]}),
        )
        self.assertRedirects(response, order.get_absolute_url())
        saved = reload(order)
        self.assertEqual(saved.agreements.get().services, ["access"])
        text = documents.order_form_markdown(saved)
        self.assertIn("Studio access", text)
        self.assertNotIn("Studio planning", text)

    def test_services_are_saved_and_presented_in_catalog_order(self) -> None:
        self.client.post(
            self.url,
            payload(["studio"], **{"studio-tier": "plus", "studio-services": ["planning", "access"]}),
        )
        order = Order.objects.get()
        self.assertEqual(order.agreements.get().services, ["access", "planning"])
        text = documents.order_form_markdown(order)
        self.assertLess(text.index("Studio access"), text.index("Studio planning"))

    def test_empty_and_subset_selections_keep_the_same_tier_fee(self) -> None:
        for services in ([], ["planning"], ["access", "planning"]):
            with self.subTest(services=services):
                data = payload(["studio"], **{"studio-tier": "plus", "studio-services": services})
                response = self.client.post(self.url, data)
                order = Order.objects.latest("created")
                self.assertRedirects(response, order.get_absolute_url())
                self.assertEqual(order.agreements.get().services, services)
                self.assertEqual(order.fee_totals, {"annual": 2400, "one_time": 0})
                quote = self.client.get(reverse("agreements:quote", args=[self.program.slug]), data)
                self.assertEqual(quote.status_code, 200)
                self.assertEqual(quote.json()["display"]["total_annual"], "$2,400")
                text = documents.order_form_markdown(order)
                self.assertEqual("Studio access" in text, "access" in services)
                self.assertEqual("Studio planning" in text, "planning" in services)

        response = self.client.post(
            reverse("agreements:order_edit", args=[order.pk]),
            payload(["studio"], **{"studio-tier": "plus", "studio-services": []}),
        )
        self.assertRedirects(response, order.get_absolute_url())
        emptied = reload(order)
        self.assertEqual(emptied.agreements.get().services, [])
        self.assertEqual(emptied.fee_totals["annual"], 2400)
        agreement = workflow.offer(get_kind("order"), emptied, user=self.user)
        self.assertNotIn("Studio access", agreement.document_markdown)
        self.assertNotIn("Studio planning", agreement.document_markdown)

    def test_tiers_with_no_eligible_base_services_can_be_ordered(self) -> None:
        for services in ([], [self.program.definition["agreements"][0]["services"][1]]):
            with self.subTest(services=services):
                definition = deepcopy(self.program.definition)
                definition["agreements"][0]["services"] = services
                Program.objects.filter(pk=self.program.pk).update(definition=definition)
                response = self.client.post(self.url, payload(["studio"], **{"studio-services": []}))
                order = Order.objects.latest("created")
                self.assertRedirects(response, order.get_absolute_url())
                self.assertEqual(order.agreements.get().services, [])
                agreement = workflow.offer(get_kind("order"), order, user=self.user)
                self.assertNotIn("Studio access", agreement.document_markdown)
                self.assertNotIn("Studio planning", agreement.document_markdown)
                self.assertEqual(reload(order).fee_totals["annual"], 1200)

    def test_invalid_services_cannot_create_or_mutate_an_order(self) -> None:
        order = make_order(self.user, {"studio": {"tier": "plus", "services": ["planning"]}}, program=self.program)
        original = documents.order_form_markdown(order)
        for services in (["unknown"], ["planning"], ["materials"]):
            with self.subTest(services=services):
                data = payload(
                    ["studio"], legal_name="Must not be saved", **{"studio-tier": "basic", "studio-services": services}
                )
                self.assertEqual(self.client.post(self.url, data).status_code, 200)
                self.assertEqual(Order.objects.count(), 1)
                response = self.client.post(reverse("agreements:order_edit", args=[order.pk]), data)
                self.assertEqual(response.status_code, 200)
                unchanged = reload(order)
                self.assertEqual(unchanged.legal_name, order.legal_name)
                line = unchanged.agreements.get()
                self.assertEqual((line.tier, line.services), ("plus", ["planning"]))
                self.assertEqual(documents.order_form_markdown(unchanged), original)
                quote = self.client.get(reverse("agreements:quote", args=[self.program.slug]), data)
                self.assertEqual(quote.status_code, 400)
                self.assertNotIn("display", quote.json())

    def test_customers_cannot_set_special_terms(self) -> None:
        self.client.post(self.url, payload(**{"studio-special_terms": "Free forever"}))
        self.assertEqual(Order.objects.get().agreements.get(agreement="studio").special_terms, "")

    def test_unticking_an_agreement_removes_it_from_the_draft(self) -> None:
        self.client.post(self.url, payload())
        order = Order.objects.get()
        self.client.post(reverse("agreements:order_edit", args=[order.pk]), payload(["studio"]))
        self.assertEqual(list(order.agreements.values_list("agreement", flat=True)), ["studio"])

    def test_unchosen_agreements_and_inactive_parameters_are_not_validated(self) -> None:
        self.client.post(
            self.url,
            payload(
                ["workshop"],
                **{
                    "studio-tier": "bogus",
                    "workshop-addon_reports": "on",
                    "workshop-addon_reports_mode": "periodic",
                    "workshop-addon_reports_copies": "invalid",
                },
            ),
        )
        line = Order.objects.get().agreements.get()
        self.assertEqual(line.agreement, "workshop")
        self.assertEqual(line.addons, {"reports": {"mode": "periodic"}})

    def test_at_least_one_agreement_is_required(self) -> None:
        self.client.post(self.url, payload([]))
        self.assertFalse(Order.objects.exists())

    def test_discount_attestation_comes_from_configuration(self) -> None:
        self.client.post(self.url, payload(discount="eligible"))
        self.assertFalse(Order.objects.exists())
        self.client.post(self.url, payload(discount="eligible", discount_attestation="on"))
        self.assertEqual(Order.objects.get().fee_totals["annual"], 6300)

    def test_selected_parameters_are_required(self) -> None:
        self.client.post(self.url, payload(**{"workshop-addon_schedule": "on"}))
        self.assertFalse(Order.objects.exists())
        self.client.post(
            self.url, payload(**{"workshop-addon_schedule": "on", "workshop-addon_schedule_window": "Weekends"})
        )
        self.assertEqual(
            Order.objects.get().agreements.get(agreement="workshop").addons, {"schedule": {"window": "Weekends"}}
        )

    def test_included_addons_do_not_charge_twice(self) -> None:
        self.client.post(self.url, payload(["workshop"], **{"workshop-addon_advisor": "on"}))
        self.assertEqual(Order.objects.get().fee_totals["annual"], 7200)

    def test_quote_totals_combined_agreements_and_one_time_charges(self) -> None:
        response = self.client.get(
            reverse("agreements:quote", args=[self.program.slug]),
            {
                "agreements": ["studio", "workshop"],
                "discount": "prepaid",
                "studio-tier": "basic",
                "workshop-tier": "max",
                "workshop-addon_kit": "on",
                "workshop-addon_sessions": "on",
                "workshop-addon_sessions_hours": "2",
            },
        )
        quote = response.json()
        self.assertEqual([line["total_annual"] for line in quote["agreements"]], ["1056.00", "6546.00"])
        self.assertEqual(quote["display"]["total_annual"], "$7,602")
        self.assertEqual(quote["display"]["term_total"], "$22,656")

    def test_quote_expands_exponent_fees_for_client_cent_arithmetic(self) -> None:
        definition = deepcopy(self.program.definition)
        workshop = definition["agreements"][1]
        workshop["tiers"][0]["annual_fee"] = "1E+4"
        workshop["addons"][0]["pricing"].update(amount="1E+3", recurring=False)
        self.program.definition = definition
        self.program.full_clean()
        self.program.save()

        response = self.client.get(
            reverse("agreements:quote", args=[self.program.slug]),
            {
                "agreements": ["workshop"],
                "workshop-tier": "basic",
                "workshop-addon_kit": "on",
                "discount": "none",
            },
        )
        quote = response.json()
        # The live summary splits fees using integer cents, not floating-point numbers.
        line = quote["agreements"][0]
        self.assertEqual(line["tier_fee"], "10000")
        self.assertEqual(line["items"][0]["amount"], "1000")
        self.assertEqual(quote["display"]["total_annual"], "$11,000")

    def test_quote_rejects_invalid_counts_instead_of_silently_pricing_zero(self) -> None:
        response = self.client.get(
            reverse("agreements:quote", args=[self.program.slug]),
            {
                "agreements": ["workshop"],
                "discount": "none",
                "workshop-tier": "basic",
                "workshop-addon_sessions": "on",
                "workshop-addon_sessions_hours": "not-a-number",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("display", response.json())

    def test_builder_accepts_another_agreement_and_configured_default(self) -> None:
        definition = deepcopy(self.program.definition)
        third = deepcopy(definition["agreements"][0])
        third.update(slug="atelier", title="Example Atelier Services", short_name="Atelier", default_tier="max")
        definition["agreements"].append(third)
        Program.objects.filter(pk=self.program.pk).update(definition=definition)
        page = self.client.get(self.url)
        self.assertEqual(page.context["builder"].agreement_forms["atelier"]["tier"].value(), "max")
        self.client.post(self.url, payload(["atelier"], **{"atelier-tier": "max"}))
        order = Order.objects.get()
        self.assertEqual(order.agreements.get().agreement, "atelier")
        self.assertEqual(order.fee_totals["annual"], 4800)

    def test_removed_catalog_selection_can_be_corrected_before_signing(self) -> None:
        order = make_order(self.user, program=self.program)
        definition = deepcopy(self.program.definition)
        definition["agreements"] = definition["agreements"][1:]
        Program.objects.filter(pk=self.program.pk).update(definition=definition)
        listing = self.client.get(reverse("agreements:order_list"))
        self.assertContains(listing, "Review selections")
        self.assertContains(listing, reverse("agreements:order_edit", args=[order.pk]))
        self.assertNotContains(listing, "$2,400")
        self.assertContains(
            self.client.get(order.get_absolute_url()), reverse("agreements:order_edit", args=[order.pk])
        )
        self.client.post(reverse("agreements:order_edit", args=[order.pk]), payload(["workshop"]))
        self.assertEqual(reload(order).agreements.get().agreement, "workshop")

    def test_removed_tier_requires_draft_review_but_leaves_offered_order_intact(self) -> None:
        draft = make_order(self.user, program=self.program)
        offered = make_order(self.user, program=self.program)
        workflow.offer(get_kind("order"), offered, user=self.user)
        definition = deepcopy(self.program.definition)
        studio = definition["agreements"][0]
        studio["tiers"] = [tier for tier in studio["tiers"] if tier["key"] != "plus"]
        studio["services"][1]["tiers"] = ["max"]
        Program.objects.filter(pk=self.program.pk).update(definition=definition)
        listing = self.client.get(reverse("agreements:order_list"))
        self.assertContains(listing, "Review selections", count=1)
        self.assertContains(listing, "$2,400", count=1)
        self.assertContains(
            self.client.get(draft.get_absolute_url()), reverse("agreements:order_edit", args=[draft.pk])
        )
        self.assertContains(self.client.get(offered.get_absolute_url()), "Plus")
        self.client.post(reverse("agreements:order_edit", args=[draft.pk]), payload(["studio"]))
        self.assertEqual(reload(draft).fee_totals["annual"], 1200)
        self.assertEqual(reload(offered).fee_totals["annual"], 2400)

    def test_unavailable_draft_services_require_review_in_customer_and_staff_lists(self) -> None:
        draft = make_order(self.user, {"studio": {"tier": "plus", "services": ["planning"]}}, program=self.program)
        offered = make_order(self.user, {"studio": {"tier": "plus", "services": ["planning"]}}, program=self.program)
        workflow.offer(get_kind("order"), offered, user=self.user)
        officer = make_officer()
        for change in ("removed", "tier_restricted"):
            definition = deepcopy(self.program.definition)
            if change == "removed":
                definition["agreements"][0]["services"] = definition["agreements"][0]["services"][:1]
            else:
                definition["agreements"][0]["services"][1]["tiers"] = ["max"]
            Program.objects.filter(pk=self.program.pk).update(definition=definition)
            for user, url in (
                (self.user, reverse("agreements:order_list")),
                (self.user, self.program.get_absolute_url()),
                (officer, reverse("agreements:staff_orders")),
            ):
                with self.subTest(change=change, url=url):
                    self.client.force_login(user)
                    listing = self.client.get(url)
                    self.assertContains(listing, "Review selections", count=1)
                    self.assertContains(listing, reverse("agreements:order_edit", args=[draft.pk]))
                    self.assertContains(listing, offered.get_absolute_url())

    def test_withdrawn_service_scope_requires_correction_against_the_live_catalog(self) -> None:
        for change in ("removed", "tier_restricted"):
            with self.subTest(change=change):
                Program.objects.filter(pk=self.program.pk).update(definition=self.program.definition)
                order = make_order(
                    self.user, {"studio": {"tier": "plus", "services": ["planning"]}}, program=self.program
                )
                agreement = workflow.offer(get_kind("order"), order, user=self.user)
                original = agreement.document_markdown
                original_sha256 = agreement.document_sha256
                original_preview = documents.order_form_markdown(reload(order))
                self.assertIn("Studio planning", original)
                self.assertNotIn("Studio access", original)
                definition = deepcopy(self.program.definition)
                studio = definition["agreements"][0]
                if change == "removed":
                    studio["services"] = studio["services"][:1]
                else:
                    studio["services"][1]["tiers"] = ["max"]
                Program.objects.filter(pk=self.program.pk).update(definition=definition)

                frozen = reload(order)
                self.assertEqual(documents.order_form_markdown(frozen), original_preview)
                self.assertEqual([service.key for service in frozen.agreement_list[0].selected_services], ["planning"])
                self.assertContains(self.client.get(order.get_absolute_url()), "Studio planning")
                workflow.withdraw(agreement, user=self.user)
                reopened = reload(order)
                self.assertEqual(reopened.agreements.get().services, ["planning"])
                edit_url = reverse("agreements:order_edit", args=[order.pk])
                self.assertContains(self.client.get(order.get_absolute_url()), edit_url)
                agreement_count = Agreement.objects.count()
                response = self.client.post(reverse("agreements:order_offer", args=[order.pk]))
                self.assertRedirects(response, order.get_absolute_url())
                rejected = reload(order)
                self.assertIsNone(rejected.agreement)
                self.assertEqual(rejected.catalog_snapshot, {})
                self.assertEqual(rejected.agreements.get().services, ["planning"])
                self.assertEqual(rejected.agreements.get().pricing, {})
                self.assertEqual(Agreement.objects.count(), agreement_count)

                response = self.client.post(
                    edit_url, payload(["studio"], **{"studio-tier": "plus", "studio-services": ["access"]})
                )
                self.assertRedirects(response, order.get_absolute_url())
                replacement = workflow.offer(get_kind("order"), reload(order), user=self.user)
                self.assertIn("Studio access", replacement.document_markdown)
                self.assertNotIn("Studio planning", replacement.document_markdown)
                agreement.refresh_from_db()
                self.assertEqual(agreement.document_markdown, original)
                self.assertEqual(agreement.document_sha256, original_sha256)


class PrivateProgramTests(TestCase):
    def setUp(self) -> None:
        self.program = make_program(is_public=False)
        self.customer = User.objects.create_user("ada", "ada@example.com", "password")
        self.other = User.objects.create_user("eve", "eve@example.com", "password")
        self.officer = make_officer()
        self.order = make_order(self.officer, program=self.program, customer_account=self.customer)
        self.create_url = reverse("agreements:order_create", args=[self.program.slug])
        self.quote_url = reverse("agreements:quote", args=[self.program.slug])

    def test_catalog_paths_are_hidden_even_from_assigned_customers(self) -> None:
        for user in (None, self.other, self.customer):
            with self.subTest(user=user):
                if user:
                    self.client.force_login(user)
                else:
                    self.client.logout()
                self.assertNotContains(self.client.get(reverse("agreements:program_list")), self.program.title)
                for url in (self.program.get_absolute_url(), self.create_url, self.quote_url):
                    self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(self.create_url, payload()).status_code, 404)
        self.assertEqual(Order.objects.count(), 1)

    def test_staff_can_browse_and_prepare_private_orders(self) -> None:
        self.client.force_login(self.officer)
        self.assertContains(self.client.get(self.program.get_absolute_url()), "Example Workshop Services")
        self.assertEqual(
            self.client.post(self.create_url, payload(customer_account_email="ada@example.com")).status_code, 302
        )
        self.assertEqual(Order.objects.filter(customer_account=self.customer).count(), 2)

    def test_assigned_customer_can_edit_quote_and_sign_existing_order_only(self) -> None:
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.order.get_absolute_url()).status_code, 200)
        page = self.client.get(reverse("agreements:order_edit", args=[self.order.pk]))
        self.assertNotContains(page, "Example Workshop Services")
        self.assertEqual(set(page.context["builder"].agreement_forms), {"studio"})
        quote = self.client.get(
            self.quote_url,
            cast(
                "dict[str, Any]",
                {
                    "order": self.order.pk,
                    "agreements": ["studio"],
                    "discount": "none",
                    "studio-tier": "max",
                },
            ),
        )
        self.assertEqual(quote.json()["display"]["total_annual"], "$4,800")
        self.client.post(
            reverse("agreements:order_edit", args=[self.order.pk]), payload(["studio"], **{"studio-tier": "max"})
        )
        self.assertEqual(reload(self.order).fee_totals["annual"], 4800)
        seen = agreement_documents.sha256(documents.compose_order_form_markdown(reload(self.order)))
        self.client.post(
            reverse("agreements:order_sign", args=[self.order.pk]),
            {
                "signer_name": "Ada Byron",
                "signer_title": "CEO",
                "accept": "on",
                "document_sha256": seen,
            },
        )
        self.assertEqual(reload(self.order).status, Agreement.Status.SIGNED)

    def test_customer_cannot_add_an_unselected_private_agreement(self) -> None:
        self.client.force_login(self.customer)
        self.client.post(reverse("agreements:order_edit", args=[self.order.pk]), payload())
        self.assertEqual(list(self.order.agreements.values_list("agreement", flat=True)), ["studio"])
        quote = self.client.get(self.quote_url, {"order": self.order.pk, **payload()})
        self.assertEqual(quote.status_code, 400)
        self.assertNotContains(quote, "Workshop", status_code=400)

    def test_order_query_parameter_cannot_bypass_authorization(self) -> None:
        for user in (None, self.other):
            with self.subTest(user=user):
                if user:
                    self.client.force_login(user)
                else:
                    self.client.logout()
                response = self.client.get(self.quote_url, {"order": self.order.pk, **payload(["studio"])})
                self.assertEqual(response.status_code, 404)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.quote_url, {"order": "not-an-order"}).status_code, 404)

    def test_private_customer_reads_only_terms_selected_for_their_order(self) -> None:
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("agreements:terms", args=["studio-terms"])).status_code, 200)
        self.assertEqual(self.client.get(reverse("agreements:terms", args=["workshop-terms"])).status_code, 404)
