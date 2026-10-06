"""Group boundaries must hold independently of staff flags and Django permissions."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.agreements import workflow
from apps.agreements.auth import EDITORS
from apps.agreements.models import Agreement, SignedCopy
from apps.agreements.tests.test_agreements import PDF, make_officer, offer_contract


class SigningGroupAccessTests(TestCase):
    def setUp(self) -> None:
        self.administrator = make_officer()
        users = get_user_model().objects
        self.customer = users.create_user("customer", "customer@example.com", "password")
        self.editor = users.create_user("editor", "editor@example.com", "password", is_staff=True)
        self.editor.groups.add(Group.objects.get_or_create(name=EDITORS)[0])
        self.staff = users.create_user("staff", "staff@example.com", "password", is_staff=True)
        self.superuser = users.create_superuser("root", "root@example.com", "password")
        self.permissions_only = users.create_user("permissions", "permissions@example.com", "password", is_staff=True)
        Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Agreement),
            codename="manage_agreement",
            defaults={"name": "Legacy agreement permission"},
        )
        self.permissions_only.user_permissions.set(Permission.objects.filter(content_type__app_label="agreements"))
        self.agreement = offer_contract(self.administrator, counterparty_account=self.customer)

    def test_staff_superuser_and_direct_permissions_do_not_grant_record_access(self) -> None:
        copy = SignedCopy.objects.create(
            agreement=self.agreement,
            kind=SignedCopy.Kind.CUSTOMER,
            filename="signed.pdf",
            content=PDF,
            sha256="0" * 64,
            uploaded_by=self.administrator,
        )
        for user in (self.staff, self.superuser, self.permissions_only):
            self.client.force_login(user)
            with self.subTest(user=user.username):
                self.assertEqual(self.client.get(reverse("agreements:queue")).status_code, 403)
                self.assertEqual(self.client.get(self.agreement.get_absolute_url()).status_code, 404)
                self.assertEqual(
                    self.client.get(reverse("agreements:document", args=[self.agreement.pk, "pdf"])).status_code, 404
                )
                self.assertEqual(
                    self.client.get(
                        reverse("agreements:copy_download", args=[self.agreement.pk, copy.kind])
                    ).status_code,
                    404,
                )

    def test_editor_can_read_but_cannot_modify_or_send_an_offer(self) -> None:
        self.client.force_login(self.editor)
        page = self.client.get(self.agreement.get_absolute_url())
        self.assertContains(page, self.agreement.counterparty_name)
        edit_url = reverse("agreements:edit", args=[self.agreement.pk])
        send_url = reverse("agreements:send_link", args=[self.agreement.pk])
        self.assertNotContains(page, edit_url)
        self.assertNotContains(page, send_url)
        self.assertEqual(self.client.get(edit_url).status_code, 403)
        self.assertEqual(
            self.client.post(
                edit_url,
                {
                    "markdown": self.agreement.document_markdown + "\nChanged by editor.",
                    "note": "Not allowed",
                    "base_sha256": self.agreement.document_sha256,
                },
            ).status_code,
            403,
        )
        self.assertEqual(self.client.post(send_url, {"name": "Signer", "email": "signer@example.com"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("agreements:withdraw", args=[self.agreement.pk])).status_code, 404)
        self.assertEqual(
            self.client.post(
                reverse("agreements:record_copy", args=[self.agreement.pk]),
                {
                    "signed_copy": SimpleUploadedFile("signed.pdf", PDF),
                    "signer_name": "Signer",
                    "signer_title": "Director",
                    "signer_email": "signer@example.com",
                    "signed_on": "2026-01-01",
                    "matches": "on",
                    "document_sha256": self.agreement.document_sha256,
                },
            ).status_code,
            404,
        )
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.OFFERED)
        self.assertEqual(self.agreement.revision, 1)
        self.assertFalse(self.agreement.signing_links.exists())
        self.assertFalse(self.agreement.signed_copies.exists())
        self.assertEqual(mail.outbox, [])

    def test_only_administrators_can_countersign_decline_or_resend(self) -> None:
        signed = workflow.sign(
            self.agreement,
            workflow.Signature("Customer", "Director", self.customer.email),
            seen_sha256=self.agreement.document_sha256,
        )
        for user in (self.editor, self.staff, self.superuser, self.permissions_only):
            self.client.force_login(user)
            for name, data in (
                ("countersign", {"name": "Officer", "title": "Director", "accept": "on"}),
                ("decline", {"reason": "Not allowed"}),
            ):
                with self.subTest(user=user.username, action=name):
                    self.assertEqual(
                        self.client.post(reverse(f"agreements:{name}", args=[signed.pk]), data).status_code, 403
                    )
        signed.refresh_from_db()
        self.assertEqual(signed.status, Agreement.Status.SIGNED)
        self.client.force_login(self.administrator)
        response = self.client.post(
            reverse("agreements:countersign", args=[signed.pk]),
            {
                "name": "Officer",
                "title": "Director",
                "accept": "on",
                "executed_copy": SimpleUploadedFile("executed.pdf", PDF),
            },
        )
        self.assertEqual(response.status_code, 302)
        signed.refresh_from_db()
        self.assertEqual(signed.status, Agreement.Status.EXECUTED)
        self.assertEqual(signed.countersigned_by, self.administrator)
        self.assertEqual(len(mail.outbox), 1)
        for user in (self.editor, self.staff, self.superuser, self.permissions_only):
            self.client.force_login(user)
            with self.subTest(user=user.username, action="resend"):
                self.assertEqual(
                    self.client.post(reverse("agreements:resend_executed_copy", args=[signed.pk])).status_code, 403
                )
        self.assertEqual(len(mail.outbox), 1)

    def test_role_removal_revokes_access_even_for_the_offer_creator(self) -> None:
        self.client.force_login(self.administrator)
        self.assertContains(self.client.get(self.agreement.get_absolute_url()), self.agreement.counterparty_name)
        self.administrator.groups.clear()
        self.assertEqual(self.client.get(reverse("agreements:queue")).status_code, 403)
        self.assertEqual(self.client.get(self.agreement.get_absolute_url()).status_code, 404)
        self.assertEqual(
            self.client.post(
                reverse("agreements:send_link", args=[self.agreement.pk]),
                {
                    "name": "Signer",
                    "email": "signer@example.com",
                },
            ).status_code,
            403,
        )
        self.assertFalse(self.agreement.signing_links.exists())

    def test_customer_and_anonymous_link_rights_do_not_require_group_membership(self) -> None:
        self.client.force_login(self.customer)
        self.assertContains(self.client.get(self.agreement.get_absolute_url()), self.agreement.counterparty_name)
        self.assertEqual(self.client.get(reverse("agreements:queue")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(self.agreement.get_absolute_url()).status_code, 302)
        self.assertEqual(self.client.get(reverse("agreements:queue")).status_code, 302)
        link, token = workflow.create_signing_link(
            self.agreement, name="Invited", email="invited@example.com", user=self.administrator
        )
        url = reverse("agreements:sign_link", args=[token])
        self.assertContains(self.client.get(url), self.agreement.counterparty_name)
        response = self.client.post(
            url,
            {
                "signer_name": "Invited",
                "signer_title": "Director",
                "accept": "on",
                "document_sha256": self.agreement.document_sha256,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.agreement.refresh_from_db()
        link.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.SIGNED)
        self.assertEqual(self.agreement.signer_email, "invited@example.com")
        self.assertIsNotNone(link.used_at)
        self.assertEqual(self.client.get(url).status_code, 410)

    def test_inactive_group_member_cannot_use_management_views(self) -> None:
        self.administrator.is_active = False
        self.administrator.save(update_fields=["is_active"])
        self.client.force_login(self.administrator)
        response = self.client.get(reverse("agreements:queue"))
        self.assertEqual(response.status_code, 302)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, Agreement.Status.OFFERED)
