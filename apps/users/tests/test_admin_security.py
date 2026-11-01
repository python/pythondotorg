"""User administration cannot grant authority or take over privileged accounts."""

from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from tastypie.models import ApiKey

from apps.agreements.auth import ADMINISTRATORS, EDITORS, can_prepare
from apps.sponsors.manage.views import SponsorshipAdminRequiredMixin
from apps.users.models import User


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class UserAdminSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editors, _ = Group.objects.get_or_create(name=EDITORS)
        cls.administrators, _ = Group.objects.get_or_create(name=ADMINISTRATORS)
        cls.sponsorship_admins, _ = Group.objects.get_or_create(name=SponsorshipAdminRequiredMixin.group_required)
        cls.social_group = Group.objects.create(name="User admin test social group")
        cls.permission = Permission.objects.get(content_type__app_label="users", codename="change_user")
        cls.operator = cls.make_user("operator", is_staff=True)
        cls.operator.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="users",
                codename__in=("view_user", "change_user", "delete_user"),
            ),
            *Permission.objects.filter(
                content_type__app_label="tastypie",
                codename__in=("view_apikey", "change_apikey", "delete_apikey"),
            ),
        )
        cls.ordinary = cls.make_user("ordinary")
        cls.ordinary.groups.add(cls.social_group)
        cls.superuser = cls.make_user("superuser", is_staff=True, is_superuser=True)
        cls.staff = cls.make_user("staff", is_staff=True)
        cls.editor = cls.make_user("editor")
        cls.editor.groups.add(cls.editors)
        cls.administrator = cls.make_user("administrator")
        cls.administrator.groups.add(cls.administrators)
        cls.sponsorship_admin = cls.make_user("sponsorship-admin")
        cls.sponsorship_admin.groups.add(cls.sponsorship_admins)
        cls.permission_holder = cls.make_user("permission-holder")
        cls.permission_holder.user_permissions.add(cls.permission)
        cls.group_permission_holder = cls.make_user("group-permission-holder")
        permission_group = Group.objects.create(name="User admin test permissions")
        permission_group.permissions.add(cls.permission)
        cls.group_permission_holder.groups.add(permission_group)
        cls.inactive_editor = cls.make_user("inactive-editor", is_active=False)
        cls.inactive_editor.groups.add(cls.editors)

    @classmethod
    def make_user(cls, username, **kwargs):
        return User.objects.create_user(
            username=username, email=f"{username}@example.com", password="original-password", **kwargs
        )

    def setUp(self):
        self.client.force_login(self.operator)
        self.user_admin = admin.site.get_model_admin(User)
        self.changelist_url = reverse("admin:users_user_changelist")

    def protected_users(self):
        return (
            self.operator,
            self.superuser,
            self.staff,
            self.editor,
            self.administrator,
            self.sponsorship_admin,
            self.permission_holder,
            self.group_permission_holder,
            self.inactive_editor,
        )

    def change_url(self, user):
        return reverse("admin:users_user_change", args=(user.pk,))

    def profile_data(self, user):
        response = self.client.get(self.change_url(user))
        self.assertEqual(response.status_code, 200)
        data = {
            "username": user.username,
            "first_name": "Updated",
            "last_name": user.last_name,
            "email": user.email,
            "bio": "Updated profile",
            "date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": user.date_joined.strftime("%H:%M:%S"),
            "groups": list(user.groups.values_list("pk", flat=True)),
            "user_permissions": list(user.user_permissions.values_list("pk", flat=True)),
            "_save": "Save",
        }
        data.update({field: "on" for field in ("is_active", "is_staff", "is_superuser") if getattr(user, field)})
        for inline in response.context["inline_admin_formsets"]:
            formset = inline.formset
            data.update({f"{formset.prefix}-{name}": value for name, value in formset.management_form.initial.items()})
            for form in formset.initial_forms:
                values = {
                    form.add_prefix(name): field.prepare_value(form.initial.get(name, field.initial))
                    for name, field in form.fields.items()
                }
                data.update({name: value for name, value in values.items() if value is not None and value is not False})
        return data

    def test_staff_cannot_enroll_self_in_any_agreements_role(self):
        for role in (self.editors, self.administrators, self.sponsorship_admins):
            with self.subTest(role=role.name):
                response = self.client.post(
                    self.change_url(self.operator),
                    {"groups": [role.pk], "is_superuser": "on", "is_staff": "on", "_save": "Save"},
                )
                self.assertEqual(response.status_code, 403)
                self.operator.refresh_from_db()
                self.assertFalse(self.operator.groups.exists())
                self.assertFalse(self.operator.is_superuser)
                self.assertFalse(can_prepare(self.operator))

    def test_forged_privilege_fields_are_excluded_from_ordinary_user_form(self):
        response = self.client.get(self.change_url(self.ordinary))
        for field in ("groups", "user_permissions", "is_staff", "is_superuser"):
            self.assertNotIn(field, response.context["adminform"].form.fields)
        data = self.profile_data(self.ordinary)
        data.update(
            groups=[self.editors.pk, self.administrators.pk, self.sponsorship_admins.pk],
            user_permissions=[self.permission.pk],
            is_staff="on",
            is_superuser="on",
        )
        response = self.client.post(self.change_url(self.ordinary), data)
        self.assertEqual(response.status_code, 302)
        self.ordinary.refresh_from_db()
        self.assertEqual(self.ordinary.first_name, "Updated")
        self.assertFalse(self.ordinary.is_staff)
        self.assertFalse(self.ordinary.is_superuser)
        self.assertFalse(self.ordinary.user_permissions.exists())
        self.assertEqual(list(self.ordinary.groups.all()), [self.social_group])
        self.assertFalse(can_prepare(self.ordinary))

    def test_ordinary_profile_edit_preserves_omitted_group_membership(self):
        data = self.profile_data(self.ordinary)
        data.pop("groups")
        data.pop("user_permissions")
        data["username"] = "updated-ordinary"
        data["email"] = "updated-ordinary@example.com"
        response = self.client.post(self.change_url(self.ordinary), data)
        self.assertEqual(response.status_code, 302)
        self.ordinary.refresh_from_db()
        self.assertEqual(self.ordinary.username, "updated-ordinary")
        self.assertEqual(self.ordinary.email, "updated-ordinary@example.com")
        self.assertEqual(list(self.ordinary.groups.all()), [self.social_group])

    def test_privileged_profiles_cannot_be_changed_or_deactivated(self):
        for user in self.protected_users():
            with self.subTest(user=user.username):
                original = (user.username, user.email, user.password, user.is_active)
                groups = list(user.groups.values_list("pk", flat=True))
                permissions = list(user.user_permissions.values_list("pk", flat=True))
                response = self.client.post(
                    self.change_url(user),
                    {
                        "username": "taken-over",
                        "email": "attacker@example.com",
                        "password": "forged-password",
                        "groups": [],
                        "user_permissions": [],
                        "_save": "Save",
                    },
                )
                self.assertEqual(response.status_code, 403)
                user.refresh_from_db()
                self.assertEqual((user.username, user.email, user.password, user.is_active), original)
                self.assertEqual(list(user.groups.values_list("pk", flat=True)), groups)
                self.assertEqual(list(user.user_permissions.values_list("pk", flat=True)), permissions)

    def test_privileged_password_change_and_disable_paths_are_denied(self):
        for user in self.protected_users():
            with self.subTest(user=user.username):
                password = user.password
                url = reverse("admin:auth_user_password_change", args=(user.pk,))
                self.assertEqual(self.client.get(url).status_code, 403)
                for data in (
                    {"password1": "new-secure-password", "password2": "new-secure-password"},
                    {"usable_password": "false", "unset-password": "Disable password"},
                ):
                    self.assertEqual(self.client.post(url, data).status_code, 403)
                    user.refresh_from_db()
                    self.assertEqual(user.password, password)

    def test_privileged_api_keys_are_not_exposed_as_readonly_inlines(self):
        for user in self.protected_users():
            with self.subTest(user=user.username):
                response = self.client.get(self.change_url(user))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["inline_admin_formsets"], [])
                key = ApiKey.objects.get(user=user)
                self.assertNotContains(response, key.key)
                response = self.client.post(
                    self.change_url(user),
                    {
                        "api_key-TOTAL_FORMS": "1",
                        "api_key-INITIAL_FORMS": "1",
                        "api_key-0-id": key.pk,
                        "api_key-0-DELETE": "on",
                        "_save": "Save",
                    },
                )
                self.assertEqual(response.status_code, 403)
                self.assertTrue(ApiKey.objects.filter(pk=key.pk).exists())

    def test_privileged_single_and_bulk_deletion_are_denied(self):
        for user in self.protected_users():
            with self.subTest(user=user.username):
                url = reverse("admin:users_user_delete", args=(user.pk,))
                self.assertEqual(self.client.post(url, {"post": "yes"}).status_code, 403)
                response = self.client.post(
                    self.changelist_url,
                    {
                        "action": "delete_selected",
                        "_selected_action": [self.ordinary.pk, user.pk],
                        "post": "yes",
                    },
                )
                self.assertEqual(response.status_code, 403)
                self.assertTrue(User.objects.filter(pk=user.pk).exists())
                self.assertTrue(User.objects.filter(pk=self.ordinary.pk).exists())

    def test_delete_queryset_enforces_target_authorization(self):
        request = RequestFactory().post(self.changelist_url)
        request.user = self.operator
        queryset = User.objects.filter(pk__in=(self.ordinary.pk, self.editor.pk))
        with self.assertRaises(PermissionDenied):
            self.user_admin.delete_queryset(request, queryset)
        self.assertEqual(queryset.count(), 2)

    def test_changelist_cannot_change_privileged_active_status(self):
        for user in self.protected_users():
            with self.subTest(user=user.username):
                was_active = user.is_active
                data = {
                    "form-TOTAL_FORMS": "2",
                    "form-INITIAL_FORMS": "2",
                    "form-0-id": self.ordinary.pk,
                    "form-1-id": user.pk,
                    "_save": "Save",
                }
                if not was_active:
                    data["form-1-is_active"] = "on"
                response = self.client.post(self.changelist_url, data)
                self.assertEqual(response.status_code, 403)
                user.refresh_from_db()
                self.ordinary.refresh_from_db()
                self.assertEqual(user.is_active, was_active)
                self.assertTrue(self.ordinary.is_active)

    def test_ordinary_changelist_active_edit_is_preserved(self):
        response = self.client.post(
            self.changelist_url,
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-0-id": self.ordinary.pk,
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.ordinary.refresh_from_db()
        self.assertFalse(self.ordinary.is_active)

    def test_ordinary_password_change_is_preserved(self):
        response = self.client.post(
            reverse("admin:auth_user_password_change", args=(self.ordinary.pk,)),
            {"password1": "new-secure-password", "password2": "new-secure-password"},
        )
        self.assertEqual(response.status_code, 302)
        self.ordinary.refresh_from_db()
        self.assertTrue(self.ordinary.check_password("new-secure-password"))

    def test_ordinary_bulk_deletion_is_preserved(self):
        response = self.client.post(
            self.changelist_url,
            {"action": "delete_selected", "_selected_action": [self.ordinary.pk], "post": "yes"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.ordinary.pk).exists())

    def test_superuser_can_assign_privileges_and_edit_privileged_profiles(self):
        self.client.force_login(self.superuser)
        self.assertFalse(can_prepare(self.superuser))
        data = self.profile_data(self.ordinary)
        data.update(
            groups=[self.editors.pk, self.administrators.pk],
            user_permissions=[self.permission.pk],
            is_staff="on",
            is_superuser="on",
        )
        response = self.client.post(self.change_url(self.ordinary), data)
        self.assertEqual(response.status_code, 302)
        self.ordinary.refresh_from_db()
        self.assertTrue(self.ordinary.is_staff)
        self.assertTrue(self.ordinary.is_superuser)
        self.assertSetEqual(set(self.ordinary.groups.all()), {self.editors, self.administrators})
        self.assertEqual(list(self.ordinary.user_permissions.all()), [self.permission])
        data = self.profile_data(self.editor)
        data["email"] = "editor-updated@example.com"
        self.assertEqual(self.client.post(self.change_url(self.editor), data).status_code, 302)
        self.editor.refresh_from_db()
        self.assertEqual(self.editor.email, "editor-updated@example.com")
        self.assertEqual(list(self.editor.groups.all()), [self.editors])
        url = reverse("admin:auth_user_password_change", args=(self.editor.pk,))
        response = self.client.post(url, {"password1": "new-secure-password", "password2": "new-secure-password"})
        self.assertEqual(response.status_code, 302)
        self.editor.refresh_from_db()
        self.assertTrue(self.editor.check_password("new-secure-password"))
