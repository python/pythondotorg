from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.agreements.auth import ADMINISTRATORS
from apps.agreements.models import Agreement, CustomContract, Terms
from apps.agreements.tests.catalog_data import make_program
from apps.agreements.tests.test_agreements import make_officer, offer_contract
from apps.agreements.tests.test_orders import make_order


class AuthoringValidationTests(TestCase):
    def setUp(self):
        self.officer = make_officer()
        self.client.force_login(self.officer)

    def test_terms_images_are_rejected_before_save_preview_or_publish(self):
        terms = Terms.objects.create(slug="example", title="Example", draft_markdown="Original draft")
        url = reverse("agreements:terms_edit", args=[terms.slug])
        for action in ({"action": "save"}, {"preview": "1"}, {"action": "publish", "version": "v1", "notes": "First"}):
            with self.subTest(action=action):
                response = self.client.post(url, {"markdown": "![image](https://example.com/image.png)", **action})
                self.assertEqual(response.status_code, 400)
                self.assertIn("markdown", response.context["form"].errors)
                terms.refresh_from_db()
                self.assertEqual(terms.draft_markdown, "Original draft")
                self.assertFalse(terms.versions.exists())

    def test_custom_contract_images_are_rejected_before_create_or_edit(self):
        data = {"title": "Example", "counterparty_name": "Example company", "body_markdown": "![image](/etc/passwd)"}
        response = self.client.post(reverse("agreements:custom_create"), data)
        self.assertIn("body_markdown", response.context["form"].errors)
        self.assertFalse(CustomContract.objects.exists())
        contract = CustomContract.objects.create(
            title="Example",
            counterparty_name="Example company",
            body_markdown="Original draft",
            created_by=self.officer,
        )
        response = self.client.post(reverse("agreements:custom_edit", args=[contract.pk]), data)
        self.assertIn("body_markdown", response.context["form"].errors)
        contract.refresh_from_db()
        self.assertEqual(contract.body_markdown, "Original draft")

    def test_document_images_are_rejected_without_a_revision(self):
        agreement = offer_contract(self.officer)
        response = self.client.post(
            reverse("agreements:edit", args=[agreement.pk]),
            {
                "markdown": agreement.document_markdown + "\n![image](/etc/passwd)",
                "note": "Unsupported image",
                "base_sha256": agreement.document_sha256,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("markdown", response.context["form"].errors)
        agreement.refresh_from_db()
        self.assertEqual(agreement.revision, 1)

    def test_unpublished_terms_link_to_editor_and_non_admin_guidance(self):
        terms = Terms.objects.create(slug="unpublished", title="Unpublished")
        response = self.client.get(reverse("agreements:terms_list"))
        self.assertContains(response, f'href="{reverse("agreements:terms_edit", args=[terms.slug])}">Unpublished</a>')
        self.assertNotContains(response, reverse("admin:agreements_terms_add"))

    def test_staff_administrator_gets_terms_creation_link(self):
        admin = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        admin.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
        self.client.force_login(admin)
        response = self.client.get(reverse("agreements:terms_list"))
        self.assertContains(response, reverse("admin:agreements_terms_add"))

    def test_staff_authoring_routes_deny_customers_without_a_login_loop(self):
        terms = Terms.objects.create(slug="private", title="Private")
        contract = CustomContract.objects.create(
            title="Example", counterparty_name="Example company", body_markdown="Draft", created_by=self.officer
        )
        routes = [
            reverse("agreements:terms_list"),
            reverse("agreements:terms_edit", args=[terms.slug]),
            reverse("agreements:custom_create"),
            *(
                reverse(f"agreements:custom_{action}", args=[contract.pk])
                for action in ("detail", "edit", "offer", "delete")
            ),
        ]
        customer = get_user_model().objects.create_user("customer", "customer@example.com", "password")
        self.client.force_login(customer)
        for url in routes:
            with self.subTest(url=url, authenticated=True):
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url).status_code, 403)
        self.client.logout()
        for url in routes:
            with self.subTest(url=url, authenticated=False):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/?next=", response["Location"])

    def test_record_admin_rejects_changes_even_for_superusers(self):
        agreement = offer_contract(self.officer)
        order = make_order(self.officer, program=make_program())
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        user.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
        self.client.force_login(user)
        for instance in (agreement, order):
            with self.subTest(model=type(instance).__name__):
                model_name = type(instance).__name__.lower()
                url = reverse(f"admin:agreements_{model_name}_change", args=[instance.pk])
                self.assertNotContains(self.client.get(url), 'name="_save"')
                response = self.client.post(url, {"status": "declined", "legal_name": "Changed"})
                self.assertEqual(response.status_code, 403)
        agreement.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(agreement.status, Agreement.Status.OFFERED)
        self.assertEqual(order.legal_name, "Example Workshops, Inc.")
