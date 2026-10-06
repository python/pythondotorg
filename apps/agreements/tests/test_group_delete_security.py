"""Group deletion cannot remove agreement roles or the memberships they confer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.agreements.auth import ADMINISTRATORS, EDITORS, can_prepare, is_administrator

if TYPE_CHECKING:
    from django.db.models import QuerySet


class GroupDeletionSecurityTests(TestCase):
    def setUp(self) -> None:
        users = get_user_model().objects
        self.staff = users.create_user("group-deleter", is_staff=True)
        self.administrators = Group.objects.get_or_create(name=ADMINISTRATORS)[0]
        self.editors = Group.objects.get_or_create(name=EDITORS)[0]
        self.ordinary_group = Group.objects.create(name="Delegated group")
        self.administrator = users.create_user("agreement-administrator")
        self.administrator.groups.add(self.administrators)
        self.editor = users.create_user("agreement-editor")
        self.editor.groups.add(self.editors)
        self.client.force_login(self.staff)

    def delegated_permissions(self) -> dict[str, QuerySet[Permission]]:
        auth_permissions = Permission.objects.filter(content_type__app_label="auth")
        return {
            "view and delete groups": auth_permissions.filter(codename__in=("view_group", "delete_group")),
            "all auth permissions": auth_permissions,
        }

    def groups(self) -> tuple[Group, Group, Group]:
        return (self.administrators, self.editors, self.ordinary_group)

    def assert_groups_and_roles_intact(self) -> None:
        for group in self.groups():
            self.assertTrue(Group.objects.filter(pk=group.pk, name=group.name).exists())
        self.assertTrue(is_administrator(self.administrator))
        self.assertTrue(can_prepare(self.editor))

    def test_delegated_staff_cannot_delete_groups_directly(self) -> None:
        for label, permissions in self.delegated_permissions().items():
            self.staff.user_permissions.set(permissions)
            for group in self.groups():
                with self.subTest(permissions=label, group=group.name):
                    url = reverse("admin:auth_group_delete", args=[group.pk])
                    self.assertEqual(self.client.get(url).status_code, 403)
                    self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
                    self.assert_groups_and_roles_intact()

    def test_delegated_staff_cannot_bulk_delete_groups(self) -> None:
        for label, permissions in self.delegated_permissions().items():
            self.staff.user_permissions.set(permissions)
            with self.subTest(permissions=label):
                response = self.client.post(
                    reverse("admin:auth_group_changelist"),
                    {
                        "action": "delete_selected",
                        "_selected_action": [group.pk for group in self.groups()],
                        "post": "yes",
                    },
                )
                # Without any permitted action the forged POST only renders the changelist.
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.context["action_form"])
                self.assert_groups_and_roles_intact()

    def test_superuser_can_delete_ordinary_groups(self) -> None:
        root = get_user_model().objects.create_superuser("identity-admin", "root@example.com", "password")
        self.client.force_login(root)
        retired = Group.objects.create(name="Retired group")
        root.groups.add(retired)
        response = self.client.post(reverse("admin:auth_group_delete", args=[retired.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Group.objects.filter(pk=retired.pk).exists())
        response = self.client.post(
            reverse("admin:auth_group_changelist"),
            {"action": "delete_selected", "_selected_action": [self.ordinary_group.pk], "post": "yes"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Group.objects.filter(pk=self.ordinary_group.pk).exists())
        for group in (self.administrators, self.editors):
            self.assertTrue(Group.objects.filter(pk=group.pk, name=group.name).exists())
        self.assertTrue(is_administrator(self.administrator))
        self.assertTrue(can_prepare(self.editor))
