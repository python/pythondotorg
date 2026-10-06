"""Account linkage is administered separately from draft preparation."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.agreements import documents as agreement_documents
from apps.agreements.auth import ADMINISTRATORS, EDITORS
from apps.agreements.models import Agreement, CustomContract, Order
from apps.agreements.orders import documents
from apps.agreements.tests.catalog_data import make_program
from apps.agreements.tests.test_orders import make_order, payload, reload


class CustomerLinkSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.administrator = users.create_user("administrator", "administrator@example.org")
        cls.administrator.groups.add(Group.objects.get_or_create(name=ADMINISTRATORS)[0])
        cls.editor = users.create_user("editor", "editor@example.org")
        cls.editor.groups.add(Group.objects.get_or_create(name=EDITORS)[0])
        cls.customer = users.create_user("customer", "customer@example.org")
        cls.accomplice = users.create_user("accomplice", "accomplice@example.org")
        cls.program = make_program(is_public=False)
        cls.order = make_order(cls.administrator, program=cls.program, customer_account=cls.customer)
        cls.contract = CustomContract.objects.create(
            title="Example contract",
            counterparty_name="Example Company",
            body_markdown="Original draft.",
            counterparty_account=cls.customer,
            created_by=cls.administrator,
        )

    def assert_link_field(self, url, name, *, shown):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIs(name in response.context["form"].fields, shown)
        (self.assertContains if shown else self.assertNotContains)(response, f'name="{name}"')
        return response

    def assert_order_actions_denied(self, order):
        for user in (self.editor, self.accomplice):
            with self.subTest(actor=user.username):
                self.client.force_login(user)
                self.assertFalse(order.is_customer(user))
                self.assertFalse(order.can_offer(user))
                for action in ("order_offer", "order_sign"):
                    response = self.client.post(reverse(f"agreements:{action}", args=[order.pk]))
                    self.assertEqual(response.status_code, 404)
        self.assertIsNone(reload(order).agreement)

    def contract_data(self, **overrides):
        return {
            "title": "Updated example contract",
            "counterparty_name": "Updated Example Company",
            "body_markdown": "Updated draft.",
            **overrides,
        }

    def test_editor_created_orders_stay_unlinked_with_or_without_forged_accounts(self):
        url = reverse("agreements:order_create", args=[self.program.slug])
        for public in (False, True):
            self.program.is_public = public
            self.program.save(update_fields=["is_public"])
            for email in (None, "", self.editor.email, self.accomplice.email):
                with self.subTest(public=public, email=email):
                    self.client.force_login(self.editor)
                    self.assert_link_field(url, "customer_account_email", shown=False)
                    data = payload(["studio"], **{"studio-special_terms": "Example payment terms."})
                    if email is not None:
                        data["customer_account_email"] = email
                    existing = set(Order.objects.values_list("pk", flat=True))
                    response = self.client.post(url, data)
                    self.assertEqual(response.status_code, 302)
                    created = Order.objects.exclude(pk__in=existing).get()
                    self.assertEqual(created.created_by, self.editor)
                    self.assertIsNone(created.customer_account)
                    self.assertEqual(created.agreements.get().special_terms, "Example payment terms.")
                    self.assert_order_actions_denied(created)

    def test_editor_cannot_assign_reassign_or_remove_customer_on_edit(self):
        for original in (None, self.customer):
            order = make_order(self.administrator, program=self.program, customer_account=original)
            url = reverse("agreements:order_edit", args=[order.pk])
            for email in (None, "", self.editor.email, self.accomplice.email):
                with self.subTest(original=original, email=email):
                    self.client.force_login(self.editor)
                    self.assert_link_field(url, "customer_account_email", shown=False)
                    data = payload(
                        ["studio"],
                        legal_name="Revised company",
                        **{"studio-special_terms": "Revised payment terms."},
                    )
                    if email is not None:
                        data["customer_account_email"] = email
                    self.assertEqual(self.client.post(url, data).status_code, 302)
                    order = reload(order)
                    self.assertEqual(order.customer_account, original)
                    self.assertEqual(order.created_by, self.administrator)
                    self.assertEqual(order.legal_name, "Revised company")
                    self.assertEqual(order.agreements.get().special_terms, "Revised payment terms.")
                    self.assert_order_actions_denied(order)
                    if original:
                        self.assertTrue(order.is_customer(original))
                        self.assertTrue(order.can_offer(original))

    def test_administrator_can_assign_reassign_and_remove_order_linkage(self):
        self.client.force_login(self.administrator)
        create_url = reverse("agreements:order_create", args=[self.program.slug])
        self.assert_link_field(create_url, "customer_account_email", shown=True)
        response = self.client.post(create_url, payload(["studio"], customer_account_email=self.customer.email))
        self.assertEqual(response.status_code, 302)
        order = Order.objects.exclude(pk=self.order.pk).get()
        self.assertEqual(order.customer_account, self.customer)
        edit_url = reverse("agreements:order_edit", args=[order.pk])
        response = self.assert_link_field(edit_url, "customer_account_email", shown=True)
        self.assertContains(response, f'value="{self.customer.email}"')
        for customer in (self.accomplice, None):
            with self.subTest(customer=customer):
                email = customer.email if customer else ""
                self.assertEqual(
                    self.client.post(edit_url, payload(["studio"], customer_account_email=email)).status_code, 302
                )
                order = reload(order)
                self.assertEqual(order.customer_account, customer)

    def test_public_customer_self_service_ignores_forged_account_assignment(self):
        self.program.is_public = True
        self.program.save(update_fields=["is_public"])
        self.client.force_login(self.customer)
        url = reverse("agreements:order_create", args=[self.program.slug])
        self.assert_link_field(url, "customer_account_email", shown=False)
        data = payload(["studio"], customer_account_email=self.accomplice.email)
        self.assertEqual(self.client.post(url, data).status_code, 302)
        order = Order.objects.exclude(pk=self.order.pk).get()
        self.assertEqual(order.customer_account, self.customer)
        self.assertEqual(order.created_by, self.customer)
        self.assertEqual(self.client.post(reverse("agreements:order_edit", args=[order.pk]), data).status_code, 302)
        order = reload(order)
        self.assertEqual(order.customer_account, self.customer)
        self.assertTrue(order.can_offer(self.customer))
        self.assertEqual(self.client.post(reverse("agreements:order_offer", args=[order.pk])).status_code, 302)
        self.assertEqual(reload(order).agreement.counterparty_account, self.customer)

    def test_administrator_linked_editor_retains_customer_signing_after_edit(self):
        url = reverse("agreements:order_edit", args=[self.order.pk])
        self.client.force_login(self.administrator)
        self.assertEqual(
            self.client.post(url, payload(["studio"], customer_account_email=self.editor.email)).status_code,
            302,
        )
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(url, payload(["studio"])).status_code, 302)
        order = reload(self.order)
        self.assertEqual(order.customer_account, self.editor)
        self.assertTrue(order.can_offer(self.editor))
        response = self.client.post(
            reverse("agreements:order_sign", args=[order.pk]),
            {
                "signer_name": "Example Customer",
                "signer_title": "Director",
                "accept": "on",
                "document_sha256": agreement_documents.sha256(documents.compose_order_form_markdown(order)),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(reload(order).status, Agreement.Status.SIGNED)

    def test_editor_created_custom_contracts_stay_unlinked(self):
        self.client.force_login(self.editor)
        url = reverse("agreements:custom_create")
        self.assert_link_field(url, "counterparty_account_email", shown=False)
        for email in (None, "", self.editor.email, self.accomplice.email):
            with self.subTest(email=email):
                data = self.contract_data()
                if email is not None:
                    data["counterparty_account_email"] = email
                existing = set(CustomContract.objects.values_list("pk", flat=True))
                self.assertEqual(self.client.post(url, data).status_code, 302)
                contract = CustomContract.objects.exclude(pk__in=existing).get()
                self.assertIsNone(contract.counterparty_account)
                self.assertEqual(contract.created_by, self.editor)
                self.assertEqual(contract.body_markdown, "Updated draft.")

    def test_editor_cannot_assign_reassign_or_remove_custom_contract_linkage(self):
        self.client.force_login(self.editor)
        url = reverse("agreements:custom_edit", args=[self.contract.pk])
        for original in (None, self.customer):
            self.contract.counterparty_account = original
            self.contract.save(update_fields=["counterparty_account"])
            for email in (None, "", self.editor.email, self.accomplice.email):
                with self.subTest(original=original, email=email):
                    self.assert_link_field(url, "counterparty_account_email", shown=False)
                    data = self.contract_data()
                    if email is not None:
                        data["counterparty_account_email"] = email
                    self.assertEqual(self.client.post(url, data).status_code, 302)
                    self.contract.refresh_from_db()
                    self.assertEqual(self.contract.counterparty_account, original)
                    self.assertEqual(self.contract.created_by, self.administrator)
                    self.assertEqual(self.contract.title, data["title"])
                    self.assertEqual(self.contract.counterparty_name, data["counterparty_name"])
                    self.assertEqual(self.contract.body_markdown, data["body_markdown"])

    def test_administrator_can_assign_reassign_and_remove_custom_contract_linkage(self):
        self.client.force_login(self.administrator)
        url = reverse("agreements:custom_create")
        self.assert_link_field(url, "counterparty_account_email", shown=True)
        response = self.client.post(url, self.contract_data(counterparty_account_email=self.customer.email))
        self.assertEqual(response.status_code, 302)
        contract = CustomContract.objects.exclude(pk=self.contract.pk).get()
        self.assertEqual(contract.counterparty_account, self.customer)
        url = reverse("agreements:custom_edit", args=[contract.pk])
        response = self.assert_link_field(url, "counterparty_account_email", shown=True)
        self.assertContains(response, f'value="{self.customer.email}"')
        for customer in (self.accomplice, None):
            with self.subTest(customer=customer):
                email = customer.email if customer else ""
                response = self.client.post(url, self.contract_data(counterparty_account_email=email))
                self.assertEqual(response.status_code, 302)
                contract.refresh_from_db()
                self.assertEqual(contract.counterparty_account, customer)
