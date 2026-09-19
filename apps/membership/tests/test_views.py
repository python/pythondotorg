from django.contrib.auth.models import Group
from django.test import TestCase
from waffle.models import Flag
from waffle.testutils import override_flag

from apps.users.factories import UserFactory

FLAG_NAME = "psf_membership"
MEMBERSHIP_URL = "/membership/"


class MembershipViewTests(TestCase):
    def _set_flag(self, **fields):
        # TestCase does not run on_commit callbacks.
        groups = fields.pop("groups", None)
        users = fields.pop("users", None)
        flag, _created = Flag.objects.get_or_create(name=FLAG_NAME)
        for key, value in fields.items():
            setattr(flag, key, value)
        flag.save()
        if groups is not None:
            flag.groups.set(groups)
        if users is not None:
            flag.users.set(users)
        flag.flush()
        return flag

    @override_flag(FLAG_NAME, active=False)
    def test_membership_landing_ensure_404(self):
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 404)

    @override_flag(FLAG_NAME, active=True)
    def test_membership_landing(self):
        # Ensure FlagMixin is working
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 200)

    def test_everyone_false_overrides_superuser_targeting(self):
        self._set_flag(everyone=False, superusers=True, staff=True, authenticated=True)
        user = UserFactory(is_superuser=True, is_staff=True, membership=None)
        self.client.force_login(user)
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 404)

    def test_authenticated_targeting_grants_access_to_any_logged_in_user(self):
        self._set_flag(everyone=None, authenticated=True)
        user = UserFactory(is_superuser=False, is_staff=False, membership=None)
        self.client.force_login(user)
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 200)

        self.client.logout()
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 404)

    def test_explicit_user_targeting_grants_access_only_to_that_user(self):
        targeted_user = UserFactory(membership=None)
        other_user = UserFactory(membership=None)
        self._set_flag(everyone=None, users=[targeted_user])

        self.client.force_login(targeted_user)
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(other_user)
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 404)

    def test_explicit_group_targeting_grants_access_only_to_members(self):
        targeted_group = Group.objects.create(name="psf-membership-testers")
        member = UserFactory(groups=[targeted_group], membership=None)
        non_member = UserFactory(membership=None)
        self._set_flag(everyone=None, groups=[targeted_group])

        self.client.force_login(member)
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(non_member)
        response = self.client.get(MEMBERSHIP_URL)
        self.assertEqual(response.status_code, 404)

    def test_testing_query_param_overrides_targeting_when_everyone_unset(self):
        self._set_flag(everyone=None, testing=True, superusers=True, staff=True, authenticated=True)

        response = self.client.get(MEMBERSHIP_URL, {"dwft_psf_membership": "1"})
        self.assertEqual(response.status_code, 200)

        response = self.client.get(MEMBERSHIP_URL, {"dwft_psf_membership": "0"})
        self.assertEqual(response.status_code, 404)
