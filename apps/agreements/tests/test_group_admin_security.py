"""Group administration cannot be used to acquire agreement roles."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from apps.agreements.auth import ADMINISTRATORS, EDITORS, is_administrator


class GroupAdministrationSecurityTests(TestCase):
    def setUp(self) -> None:
        users = get_user_model().objects
        self.staff = users.create_user("group-editor", is_staff=True)
        self.staff.user_permissions.set(
            Permission.objects.filter(content_type__app_label="auth", codename__in=("add_group", "change_group"))
        )
        self.own_group = Group.objects.create(name="Delegated group")
        self.staff.groups.add(self.own_group)
        self.administrators = Group.objects.get_or_create(name=ADMINISTRATORS)[0]
        self.editors = Group.objects.get_or_create(name=EDITORS)[0]
        self.administrator = users.create_user("agreement-administrator")
        self.administrator.groups.add(self.administrators)
        self.client.force_login(self.staff)

    def test_group_editor_cannot_rename_roles_or_take_their_names(self) -> None:
        for group in (self.administrators, self.editors):
            with self.subTest(role=group.name):
                original_name = group.name
                response = self.client.post(
                    reverse("admin:auth_group_change", args=[group.pk]),
                    {"name": "Renamed role", "permissions": [], "_save": "Save"},
                )
                self.assertEqual(response.status_code, 403)
                group.refresh_from_db()
                self.assertEqual(group.name, original_name)
        response = self.client.post(
            reverse("admin:auth_group_change", args=[self.own_group.pk]),
            {"name": ADMINISTRATORS, "permissions": [], "_save": "Save"},
        )
        self.assertEqual(response.status_code, 403)
        self.own_group.refresh_from_db()
        self.assertEqual(self.own_group.name, "Delegated group")
        self.assertFalse(is_administrator(self.staff))
        self.assertTrue(is_administrator(self.administrator))
        self.assertEqual(self.client.get(reverse("agreements:queue")).status_code, 403)

    def test_group_editor_cannot_grant_user_administration_to_own_group(self) -> None:
        permission = Permission.objects.get(content_type__app_label="users", codename="change_user")
        response = self.client.post(
            reverse("admin:auth_group_change", args=[self.own_group.pk]),
            {"name": self.own_group.name, "permissions": [permission.pk], "_save": "Save"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.own_group.permissions.exists())

    def test_group_creator_cannot_create_a_privileged_group(self) -> None:
        permission = Permission.objects.get(content_type__app_label="users", codename="change_user")
        response = self.client.post(
            reverse("admin:auth_group_add"),
            {"name": "New privileged group", "permissions": [permission.pk], "_save": "Save"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Group.objects.filter(name="New privileged group").exists())

    def test_delegated_group_editor_can_still_inspect_groups(self) -> None:
        response = self.client.get(reverse("admin:auth_group_change", args=[self.own_group.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_group.name)

    def test_superuser_can_create_and_manage_group_permissions(self) -> None:
        root = get_user_model().objects.create_superuser("identity-admin", "root@example.com", "password")
        self.client.force_login(root)
        permission = Permission.objects.get(content_type__app_label="users", codename="change_user")
        response = self.client.post(
            reverse("admin:auth_group_add"),
            {"name": "Trusted group", "permissions": [permission.pk], "_save": "Save"},
        )
        self.assertEqual(response.status_code, 302)
        group = Group.objects.get(name="Trusted group")
        self.assertEqual(list(group.permissions.all()), [permission])
        response = self.client.post(
            reverse("admin:auth_group_change", args=[group.pk]),
            {"name": "Renamed trusted group", "permissions": [], "_save": "Save"},
        )
        self.assertEqual(response.status_code, 302)
        group.refresh_from_db()
        self.assertEqual(group.name, "Renamed trusted group")
        self.assertFalse(group.permissions.exists())
