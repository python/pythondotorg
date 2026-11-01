"""Group-only authorization for draft authoring and read-only record administration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.agreements.auth import ADMINISTRATORS, EDITORS
from apps.agreements.models import Agreement, CustomContract, Order, Program, Terms, TermsVersion
from apps.agreements.tests.catalog_data import make_program
from apps.agreements.tests.test_agreements import offer_contract
from apps.agreements.tests.test_orders import make_order
from apps.sponsors.manage.views import SponsorshipAdminRequiredMixin

if TYPE_CHECKING:
    from apps.users.models import User


class DraftGroupRoleTests(TestCase):
    administrator: User
    editor: User
    sponsorship_admin: User
    staff: User
    superuser: User
    permission_only: User
    customer: User
    terms: Terms
    version: TermsVersion
    contract: CustomContract
    program: Program
    order: Order
    agreement: Agreement

    @classmethod
    def setUpTestData(cls) -> None:
        users = get_user_model().objects
        cls.administrator = users.create_user("administrator", "administrator@example.org", is_staff=True)
        cls.administrator.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
        cls.editor = users.create_user("editor", "editor@example.org", is_staff=True)
        cls.editor.groups.add(Group.objects.get_or_create(name=EDITORS)[0])
        cls.sponsorship_admin = users.create_user("sponsorship-admin", "sponsorships@example.org", is_staff=True)
        cls.sponsorship_admin.groups.add(
            Group.objects.get_or_create(name=SponsorshipAdminRequiredMixin.group_required)[0]
        )
        cls.staff = users.create_user("staff", "staff@example.org", is_staff=True)
        cls.superuser = users.create_superuser("superuser", "superuser@example.org", "password")
        cls.permission_only = users.create_user("permission-only", "permissions@example.org", is_staff=True)
        cls.permission_only.user_permissions.set(Permission.objects.filter(content_type__app_label="agreements"))
        cls.customer = users.create_user("customer", "customer@example.org")
        cls.terms = Terms.objects.create(
            slug="example-private", title="Example private terms", draft_markdown="Original draft", under_review=True
        )
        cls.version = TermsVersion.objects.create(terms=cls.terms, version="v1", markdown="Original published text.")
        cls.contract = CustomContract.objects.create(
            title="Example draft",
            counterparty_name="Example Company",
            body_markdown="Original draft",
            created_by=cls.editor,
        )
        cls.program = make_program(is_public=False)
        cls.order = make_order(cls.administrator, program=cls.program, customer_account=cls.customer)
        cls.agreement = offer_contract(
            cls.administrator, title="Example offered contract", terms=cls.terms, counterparty_account=cls.customer
        )

    def terms_url(self) -> str:
        return reverse("agreements:terms_edit", args=[self.terms.slug])

    def contract_data(self) -> dict[str, str]:
        return {"title": "Updated example", "counterparty_name": "Example Company", "body_markdown": "Updated draft"}

    def assert_terms_unchanged(self) -> None:
        self.terms.refresh_from_db()
        self.assertEqual(self.terms.draft_markdown, "Original draft")
        self.assertFalse(self.terms.is_public)
        self.assertTrue(self.terms.under_review)
        self.assertEqual(self.terms.versions.count(), 1)

    def test_editor_saves_and_previews_only_draft_text(self) -> None:
        self.client.force_login(self.editor)
        response = self.client.get(self.terms_url())
        self.assertContains(response, 'value="save"')
        self.assertContains(response, 'name="preview"')
        for field in ("is_public", "under_review", "version", "notes"):
            self.assertNotIn(field, response.context["form"].fields)
            self.assertNotContains(response, f'name="{field}"')
        self.assertNotContains(response, 'value="publish"')
        self.assertNotContains(self.client.get(reverse("agreements:terms_list")), reverse("admin:agreements_terms_add"))
        response = self.client.post(self.terms_url(), {"markdown": "Preview example.", "preview": "1"})
        self.assertContains(response, "Preview example.")
        self.assert_terms_unchanged()
        response = self.client.post(self.terms_url(), {"markdown": "Saved example.", "action": "save"})
        self.assertRedirects(response, self.terms_url())
        self.terms.refresh_from_db()
        self.assertEqual(self.terms.draft_markdown, "Saved example.")
        self.assertEqual(self.terms.draft_updated_by, self.editor)
        self.assertFalse(self.terms.is_public)
        self.assertTrue(self.terms.under_review)
        self.assertEqual(self.terms.versions.count(), 1)

    def test_sponsorship_admin_saves_drafts_like_an_editor(self) -> None:
        self.client.force_login(self.sponsorship_admin)
        response = self.client.post(self.terms_url(), {"markdown": "Saved example.", "action": "save"})
        self.assertRedirects(response, self.terms_url())
        self.terms.refresh_from_db()
        self.assertEqual(self.terms.draft_updated_by, self.sponsorship_admin)
        self.assertEqual(self.terms.versions.count(), 1)
        response = self.client.post(reverse("agreements:custom_create"), self.contract_data())
        contract = CustomContract.objects.get(title="Updated example")
        self.assertRedirects(response, contract.get_absolute_url())
        self.assertEqual(contract.created_by, self.sponsorship_admin)

    def test_editor_forged_publication_and_configuration_posts_are_forbidden(self) -> None:
        for user in (self.editor, self.sponsorship_admin):
            self.client.force_login(user)
            self.assert_forged_terms_posts_are_forbidden()

    def assert_forged_terms_posts_are_forbidden(self) -> None:
        for payload in (
            {"action": "publish", "version": "v2", "notes": "Changed"},
            {"action": "publish", "preview": "1"},
            {"action": "save", "is_public": "on"},
            {"action": "save", "under_review": ""},
            {"preview": "1", "is_public": ""},
            {"action": "save", "version": "v2"},
            {"action": "save", "notes": "Changed"},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(self.terms_url(), {"markdown": "Unauthorized change", **payload})
                self.assertEqual(response.status_code, 403)
                self.assert_terms_unchanged()

    def test_administrator_can_publish_and_configure_terms(self) -> None:
        self.client.force_login(self.administrator)
        response = self.client.get(self.terms_url())
        self.assertContains(response, 'value="publish"')
        self.assertContains(response, 'name="is_public"')
        response = self.client.post(
            self.terms_url(),
            {
                "action": "publish",
                "markdown": "New example publication.",
                "version": "v2",
                "notes": "Example revision",
                "is_public": "on",
            },
        )
        published = self.terms.versions.get(version="v2")
        self.assertRedirects(response, published.get_absolute_url())
        self.terms.refresh_from_db()
        self.assertTrue(self.terms.is_public)
        self.assertFalse(self.terms.under_review)
        self.assertEqual(published.published_by, self.administrator)

    def test_editor_can_create_edit_and_discard_custom_drafts_without_staff_status(self) -> None:
        self.editor.is_staff = False
        self.editor.save(update_fields=["is_staff"])
        self.client.force_login(self.editor)
        response = self.client.get(reverse("admin:agreements_customcontract_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])
        response = self.client.post(reverse("agreements:custom_create"), self.contract_data())
        contract = CustomContract.objects.get(title="Updated example")
        self.assertRedirects(response, contract.get_absolute_url())
        self.assertEqual(contract.created_by, self.editor)
        response = self.client.post(reverse("agreements:custom_edit", args=[self.contract.pk]), self.contract_data())
        self.assertRedirects(response, self.contract.get_absolute_url())
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.body_markdown, "Updated draft")
        response = self.client.get(self.contract.get_absolute_url())
        self.assertContains(response, reverse("agreements:custom_edit", args=[self.contract.pk]))
        self.assertContains(response, reverse("agreements:custom_delete", args=[self.contract.pk]))
        self.assertNotContains(response, reverse("agreements:custom_offer", args=[self.contract.pk]))
        response = self.client.post(reverse("agreements:custom_delete", args=[self.contract.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CustomContract.objects.filter(pk=self.contract.pk).exists())

    def test_only_administrator_can_offer_custom_draft(self) -> None:
        url = reverse("agreements:custom_offer", args=[self.contract.pk])
        for user in (self.editor, self.sponsorship_admin, self.staff, self.superuser, self.permission_only):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.post(url).status_code, 403)
                self.contract.refresh_from_db()
                self.assertIsNone(self.contract.agreement_id)
                self.assertEqual(Agreement.objects.count(), 1)
        self.client.force_login(self.administrator)
        self.assertContains(self.client.get(self.contract.get_absolute_url()), url)
        response = self.client.post(url)
        self.contract.refresh_from_db()
        self.assertIsNotNone(self.contract.agreement_id)
        self.assertRedirects(response, cast("Agreement", self.contract.agreement).get_absolute_url())

    def test_offered_custom_edit_redirects_editor_to_readable_record_without_mutation(self) -> None:
        self.client.force_login(self.editor)
        contract = cast("CustomContract", self.agreement.subject)
        url = reverse("agreements:custom_edit", args=[contract.pk])
        for method in (self.client.get, self.client.post):
            response = method(url, self.contract_data())
            self.assertRedirects(response, self.agreement.get_absolute_url())
        contract.refresh_from_db()
        self.agreement.refresh_from_db()
        self.assertEqual(contract.title, "Example offered contract")
        self.assertEqual(self.agreement.revision, 1)

    def test_ungrouped_staff_superuser_and_permission_holder_cannot_author(self) -> None:
        for user in (self.staff, self.superuser, self.permission_only):
            self.client.force_login(user)
            urls = (
                reverse("agreements:terms_list"),
                self.terms_url(),
                reverse("agreements:custom_create"),
                self.contract.get_absolute_url(),
                reverse("agreements:custom_edit", args=[self.contract.pk]),
                reverse("agreements:custom_delete", args=[self.contract.pk]),
            )
            for url in urls:
                with self.subTest(user=user.username, url=url):
                    self.assertEqual(self.client.get(url).status_code, 403)
                    response = self.client.post(
                        url, {**self.contract_data(), "action": "save", "markdown": "Unauthorized change"}
                    )
                    self.assertEqual(response.status_code, 403)
            response = self.client.post(
                self.terms_url(),
                {
                    "action": "publish",
                    "markdown": "Unauthorized publication",
                    "version": "v2",
                    "notes": "Unauthorized",
                    "is_public": "on",
                },
            )
            self.assertEqual(response.status_code, 403)
            self.assert_terms_unchanged()
            self.contract.refresh_from_db()
            self.assertEqual(self.contract.body_markdown, "Original draft")
            self.assertEqual(CustomContract.objects.count(), 2)

    def test_revoked_authors_and_offerers_cannot_read_private_terms(self) -> None:
        self.administrator.groups.clear()
        self.client.force_login(self.administrator)
        for terms in (self.terms, Terms.objects.get(slug="studio-terms")):
            self.assertEqual(
                self.client.get(cast("TermsVersion", terms.current_version).get_absolute_url()).status_code, 404
            )
        self.assertEqual(self.client.get(self.terms_url()).status_code, 403)
        self.editor.groups.clear()
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(self.contract.get_absolute_url()).status_code, 403)
        response = self.client.post(reverse("agreements:custom_edit", args=[self.contract.pk]), self.contract_data())
        self.assertEqual(response.status_code, 403)
        self.contract.refresh_from_db()
        self.assertEqual(self.contract.body_markdown, "Original draft")
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(self.version.get_absolute_url()), "Original published text.")
        self.assertEqual(self.client.get(Terms.objects.get(slug="studio-terms").get_absolute_url()).status_code, 200)

    def test_admin_module_and_view_permissions_use_only_groups(self) -> None:
        instances = (self.terms, self.program, self.contract, self.agreement, self.order)
        users = (
            self.editor,
            self.sponsorship_admin,
            self.administrator,
            self.staff,
            self.superuser,
            self.permission_only,
        )
        for user in users:
            allowed = user in (self.editor, self.sponsorship_admin, self.administrator)
            self.client.force_login(user)
            index = self.client.get(reverse("admin:index"))
            for instance in instances:
                name = type(instance).__name__.lower()
                with self.subTest(user=user.username, model=name):
                    url = reverse(f"admin:agreements_{name}_changelist")
                    if allowed:
                        self.assertContains(index, url)
                    else:
                        self.assertNotContains(index, url)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200 if allowed else 403)
                    response = self.client.get(reverse(f"admin:agreements_{name}_change", args=[instance.pk]))
                    self.assertEqual(response.status_code, 200 if allowed else 403)

    def test_group_members_can_view_record_inlines_without_model_permissions(self) -> None:
        for user in (self.editor, self.sponsorship_admin, self.administrator):
            self.client.force_login(user)
            self.assertFalse(user.user_permissions.exists())
            for instance, expected in (
                (self.terms, self.version),
                (self.agreement, self.agreement.revisions.get()),
                (self.order, self.order.agreements.get()),
            ):
                name = type(instance).__name__.lower()
                with self.subTest(user=user.username, model=name):
                    response = self.client.get(reverse(f"admin:agreements_{name}_change", args=[instance.pk]))
                    shown = [
                        row for inline in response.context["inline_admin_formsets"] for row in inline.formset.queryset
                    ]
                    self.assertIn(expected, shown)

    def test_admin_configuration_rejects_forged_writes_without_administrator_group(self) -> None:
        original_definition = self.program.definition
        forged_definition = {**original_definition, "order_title": "Unauthorized"}
        for user in (self.editor, self.sponsorship_admin, self.staff, self.superuser, self.permission_only):
            self.client.force_login(user)
            for instance, data in (
                (self.terms, {"slug": self.terms.slug, "title": "Unauthorized", "is_public": "on"}),
                (
                    self.program,
                    {
                        "slug": self.program.slug,
                        "title": "Unauthorized",
                        "is_public": "on",
                        "definition": json.dumps(forged_definition),
                    },
                ),
            ):
                name = type(instance).__name__.lower()
                with self.subTest(user=user.username, model=name):
                    response = self.client.post(reverse(f"admin:agreements_{name}_change", args=[instance.pk]), data)
                    self.assertEqual(response.status_code, 403)
                    response = self.client.post(
                        reverse(f"admin:agreements_{name}_add"), {**data, "slug": "new-example"}
                    )
                    self.assertEqual(response.status_code, 403)
                    response = self.client.post(
                        reverse(f"admin:agreements_{name}_delete", args=[instance.pk]), {"post": "yes"}
                    )
                    self.assertEqual(response.status_code, 403)
                    instance.refresh_from_db()
                    self.assertNotEqual(instance.title, "Unauthorized")
                    self.assertFalse(instance.is_public)
                    self.assertFalse(type(instance).objects.filter(slug="new-example").exists())
            self.assert_terms_unchanged()
            self.assertEqual(self.program.definition, original_definition)

    def test_administrator_can_create_terms_and_change_program_configuration(self) -> None:
        self.client.force_login(self.administrator)
        response = self.client.post(
            reverse("admin:agreements_terms_add"),
            {
                "slug": "new-example",
                "title": "New example terms",
                "is_public": "on",
                "versions-TOTAL_FORMS": "0",
                "versions-INITIAL_FORMS": "0",
                "versions-MIN_NUM_FORMS": "0",
                "versions-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Terms.objects.get(slug="new-example").is_public)
        Terms.objects.filter(slug__in=[item.terms_slug for item in self.program.catalog.agreements.values()]).update(
            is_public=True
        )
        response = self.client.post(
            reverse("admin:agreements_program_change", args=[self.program.pk]),
            {
                "slug": self.program.slug,
                "title": "Updated example program",
                "is_public": "on",
                "definition": json.dumps(self.program.definition),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.program.refresh_from_db()
        self.assertEqual(self.program.title, "Updated example program")
        self.assertTrue(self.program.is_public)

    def test_all_groups_and_superusers_cannot_mutate_admin_records(self) -> None:
        users = (
            self.editor,
            self.sponsorship_admin,
            self.administrator,
            self.staff,
            self.superuser,
            self.permission_only,
        )
        for user in users:
            self.client.force_login(user)
            for instance in (self.agreement, self.contract, self.order):
                name = type(instance).__name__.lower()
                with self.subTest(user=user.username, model=name):
                    response = self.client.post(reverse(f"admin:agreements_{name}_add"), self.contract_data())
                    self.assertEqual(response.status_code, 403)
                    response = self.client.post(
                        reverse(f"admin:agreements_{name}_change", args=[instance.pk]),
                        {**self.contract_data(), "status": "declined", "legal_name": "Unauthorized"},
                    )
                    self.assertEqual(response.status_code, 403)
                    response = self.client.post(
                        reverse(f"admin:agreements_{name}_delete", args=[instance.pk]), {"post": "yes"}
                    )
                    self.assertEqual(response.status_code, 403)
        self.agreement.refresh_from_db()
        self.contract.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.OFFERED)
        self.assertEqual(self.contract.body_markdown, "Original draft")
        self.assertEqual(self.order.legal_name, "Example Workshops, Inc.")
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Program.objects.count(), 1)
