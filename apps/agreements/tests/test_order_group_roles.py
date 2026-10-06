"""Order management is granted by named groups, independently of customer rights."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.agreements import documents as agreement_documents
from apps.agreements import workflow
from apps.agreements.auth import ADMINISTRATORS, EDITORS
from apps.agreements.models import Agreement, Order, Program
from apps.agreements.orders import documents
from apps.agreements.registry import get_kind
from apps.agreements.tests.catalog_data import make_program
from apps.agreements.tests.test_orders import make_officer, make_order, payload, reload

User = get_user_model()


class OrderGroupRoleTests(TestCase):
    def setUp(self):
        self.editor = User.objects.create_user("editor", "editor@example.org", "password")
        self.editors = Group.objects.get_or_create(name=EDITORS)[0]
        self.editor.groups.add(self.editors)
        self.administrator = make_officer()
        self.customer = User.objects.create_user("customer", "customer@example.com", "password")
        self.program = make_program(is_public=False)
        self.order = make_order(self.editor, program=self.program, customer_account=self.customer)
        self.offer_url = reverse("agreements:order_offer", args=[self.order.pk])
        self.quote_url = reverse("agreements:quote", args=[self.program.slug])
        self.create_url = reverse("agreements:order_create", args=[self.program.slug])

    def test_both_groups_can_read_private_catalogs_and_all_order_queues(self):
        for user in (self.editor, self.administrator):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertTrue(Program.visible_to(user).filter(pk=self.program.pk).exists())
                self.assertContains(self.client.get(self.program.get_absolute_url()), "Example Workshop Services")
                self.assertContains(self.client.get(reverse("agreements:staff_orders")), self.order.legal_name)
                self.assertContains(self.client.get(reverse("agreements:queue")), "Agreements")
                self.assertEqual(self.client.get(reverse("agreements:terms_list")).status_code, 200)
                self.assertEqual(self.client.get(self.quote_url, payload(["studio"])).status_code, 200)
                self.assertContains(self.client.get(self.order.get_absolute_url()), "All orders")

    def test_editor_can_create_edit_and_discard_unoffered_orders(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            self.create_url,
            payload(["studio"], customer_account_email=self.customer.email),
        )
        self.assertEqual(response.status_code, 302)
        created = Order.objects.exclude(pk=self.order.pk).get()
        self.assertEqual(created.created_by, self.editor)
        self.assertIsNone(created.customer_account)
        response = self.client.post(
            reverse("agreements:order_edit", args=[created.pk]),
            payload(
                ["studio"],
                legal_name="Example Revised Workshops, Inc.",
                customer_account_email=self.customer.email,
                **{"studio-special_terms": "Example payment terms."},
            ),
        )
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.legal_name, "Example Revised Workshops, Inc.")
        self.assertEqual(created.agreements.get().special_terms, "Example payment terms.")
        self.assertIsNone(created.customer_account)
        self.assertEqual(self.client.post(reverse("agreements:order_delete", args=[created.pk])).status_code, 302)
        self.assertFalse(Order.objects.filter(pk=created.pk).exists())

    def test_editor_cannot_offer_or_sign_for_the_linked_customer(self):
        self.client.force_login(self.editor)
        self.assertTrue(self.order.can_edit(self.editor))
        self.assertFalse(self.order.can_offer(self.editor))
        page = self.client.get(self.order.get_absolute_url())
        self.assertContains(page, "Discard draft")
        self.assertNotContains(page, "Make ready to sign")
        self.assertNotContains(page, "Sign Order Form")
        self.assertEqual(self.client.post(self.offer_url).status_code, 404)
        self.assertEqual(self.client.post(reverse("agreements:order_sign", args=[self.order.pk])).status_code, 404)
        self.assertIsNone(reload(self.order).agreement)

    def test_administrator_can_offer_for_another_customer(self):
        self.client.force_login(self.administrator)
        self.assertTrue(self.order.can_offer(self.administrator))
        self.assertContains(self.client.get(self.order.get_absolute_url()), "Make ready to sign")
        self.assertEqual(self.client.post(self.offer_url).status_code, 302)
        order = reload(self.order)
        self.assertEqual(order.status, Agreement.Status.OFFERED)
        self.assertEqual(order.agreement.counterparty_account, self.customer)

    def test_editor_cannot_revise_offered_documents_or_use_staff_signing_controls(self):
        agreement = workflow.offer(get_kind("order"), self.order, user=self.administrator)
        self.client.force_login(self.editor)
        page = self.client.get(self.order.get_absolute_url())
        self.assertContains(page, "Agreement record")
        for text in (
            "Make ready to sign",
            "Discard draft",
            "Edit this document",
            "Send signing link",
            "Record signed copy",
        ):
            self.assertNotContains(page, text)
        for name in ("edit", "send_link", "countersign"):
            with self.subTest(action=name):
                response = self.client.post(reverse(f"agreements:{name}", args=[agreement.pk]))
                self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post(self.offer_url).status_code, 404)
        self.assertEqual(self.client.post(reverse("agreements:order_delete", args=[self.order.pk])).status_code, 404)
        self.assertEqual(reload(self.order).agreement.document_sha256, agreement.document_sha256)

    def test_staff_superuser_and_direct_permissions_do_not_grant_management_access(self):
        staff = User.objects.create_user("staff", "staff@example.org", "password", is_staff=True)
        superuser = User.objects.create_superuser("root", "root@example.org", "password")
        permitted = User.objects.create_user("permitted", "permitted@example.org", "password")
        permission, _ = Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Agreement),
            codename="manage_agreement",
            defaults={"name": "Former agreement management permission"},
        )
        permitted.user_permissions.add(permission)
        for user in (staff, superuser, permitted):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertFalse(self.order.can_view(user))
                self.assertFalse(self.order.can_edit(user))
                self.assertFalse(self.order.can_offer(user))
                self.assertFalse(Program.visible_to(user).filter(pk=self.program.pk).exists())
                self.assertEqual(self.client.get(reverse("agreements:staff_orders")).status_code, 403)
                self.assertEqual(self.client.get(self.program.get_absolute_url()).status_code, 404)
                self.assertEqual(self.client.get(self.quote_url, payload(["studio"])).status_code, 404)
                self.assertEqual(self.client.post(self.create_url, payload(["studio"])).status_code, 404)
                self.assertEqual(self.client.get(self.order.get_absolute_url()).status_code, 404)
                self.assertEqual(self.client.post(self.offer_url).status_code, 404)
                self.assertNotContains(self.client.get(reverse("agreements:program_list")), "All orders")

    def test_revoked_creator_loses_draft_and_offered_order_access(self):
        self.editor.groups.add(Group.objects.get(name=ADMINISTRATORS))
        offered = make_order(self.editor, program=self.program, customer_account=self.customer)
        agreement = workflow.offer(get_kind("order"), offered, user=self.editor)
        self.client.force_login(self.editor)
        self.assertContains(self.client.get(reverse("agreements:order_list")), self.order.legal_name)
        self.editor.groups.clear()
        self.assertNotContains(self.client.get(reverse("agreements:order_list")), self.order.legal_name)
        self.assertFalse(agreement.can_view(self.editor))
        self.assertEqual(self.client.get(agreement.get_absolute_url()).status_code, 404)
        for order in (self.order, offered):
            with self.subTest(order=order.pk):
                self.assertFalse(order.can_view(self.editor))
                self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
                self.assertEqual(
                    self.client.get(reverse("agreements:order_document", args=[order.pk, "pdf"])).status_code, 404
                )
                for name in ("order_edit", "order_offer", "order_delete", "order_sign"):
                    response = self.client.post(reverse(f"agreements:{name}", args=[order.pk]))
                    self.assertEqual(response.status_code, 404)
                self.assertEqual(
                    self.client.get(self.quote_url, {"order": order.pk, **payload(["studio"])}).status_code, 404
                )
        self.assertEqual(self.client.get(self.program.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.get(self.quote_url, payload(["studio"])).status_code, 404)

    def test_editor_linked_to_the_order_keeps_customer_offer_rights(self):
        own = make_order(self.editor, program=self.program)
        self.client.force_login(self.editor)
        self.assertTrue(own.can_offer(self.editor))
        self.assertContains(self.client.get(own.get_absolute_url()), "Make ready to sign")
        self.assertEqual(self.client.post(reverse("agreements:order_offer", args=[own.pk])).status_code, 302)
        self.assertEqual(reload(own).status, Agreement.Status.OFFERED)

    def test_linked_customer_can_offer_and_sign_without_any_group(self):
        self.client.force_login(self.customer)
        self.assertTrue(self.order.can_offer(self.customer))
        self.assertContains(self.client.get(self.order.get_absolute_url()), "Make ready to sign")
        self.assertEqual(self.client.post(self.offer_url).status_code, 302)
        agreement = reload(self.order).agreement
        page = self.client.get(self.order.get_absolute_url())
        self.assertContains(page, "Sign on python.org")
        self.assertNotContains(page, "Send signing link")
        self.assertEqual(
            self.client.post(
                reverse("agreements:sign", args=[agreement.pk]),
                {
                    "signer_name": "Example Customer",
                    "signer_title": "Director",
                    "accept": "on",
                    "document_sha256": agreement.document_sha256,
                },
            ).status_code,
            302,
        )
        self.assertEqual(reload(self.order).status, Agreement.Status.SIGNED)

    def test_revoked_group_member_keeps_linked_customer_draft_rights(self):
        own = make_order(self.editor, program=self.program)
        self.editor.groups.remove(self.editors)
        self.client.force_login(self.editor)
        self.assertTrue(own.can_view(self.editor))
        self.assertTrue(own.can_edit(self.editor))
        self.assertTrue(own.can_offer(self.editor))
        page = self.client.get(reverse("agreements:order_list"))
        self.assertContains(page, own.get_absolute_url())
        self.assertNotContains(page, self.order.get_absolute_url())
        self.assertEqual(self.client.get(self.quote_url, {"order": own.pk, **payload(["studio"])}).status_code, 200)
        self.assertContains(self.client.get(own.get_absolute_url()), "Sign Order Form")
        response = self.client.post(
            reverse("agreements:order_sign", args=[own.pk]),
            {
                "signer_name": "Example Customer",
                "signer_title": "Director",
                "accept": "on",
                "document_sha256": agreement_documents.sha256(documents.compose_order_form_markdown(own)),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(reload(own).status, Agreement.Status.SIGNED)
