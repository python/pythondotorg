from django.contrib.auth import get_user_model
from django.http import HttpRequest, QueryDict
from django.test import TestCase
from tastypie.http import HttpUnauthorized

from pydotorg.resources import API_KEY_AUTHENTICATED_ATTR, ApiKeyOrGuestAuthentication

User = get_user_model()


class TestResources(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="passworduser",
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

    def api_key_header(self):
        return f"ApiKey {self.staff_user.username}:{self.staff_user.api_key.key}"

    def test_authentication(self):
        request = HttpRequest()
        auth = ApiKeyOrGuestAuthentication()
        self.assertTrue(auth.is_authenticated(request))
        self.assertFalse(request.user.is_authenticated)

        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = self.api_key_header()
        self.assertTrue(auth.is_authenticated(request))
        self.assertEqual(request.user, self.staff_user)
        self.assertTrue(getattr(request, API_KEY_AUTHENTICATED_ATTR))

    def test_authentication_staff_unauthorized(self):
        auth = ApiKeyOrGuestAuthentication()

        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = f"ApiKey {self.staff_user.username}:not-api-key"
        self.assertIsInstance(auth.is_authenticated(request), HttpUnauthorized)

        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = f"ApiKey not-staff:{self.staff_user.api_key.key}"
        self.assertIsInstance(auth.is_authenticated(request), HttpUnauthorized)

    def test_authentication_rejects_legacy_query_credentials(self):
        auth = ApiKeyOrGuestAuthentication()
        request = HttpRequest()
        request.GET["username"] = self.staff_user.username
        request.GET["api_key"] = self.staff_user.api_key.key

        self.assertIsInstance(auth.is_authenticated(request), HttpUnauthorized)
        self.assertFalse(getattr(request, API_KEY_AUTHENTICATED_ATTR))

    def test_authentication_rejects_legacy_form_credentials(self):
        auth = ApiKeyOrGuestAuthentication()
        request = HttpRequest()
        request.method = "POST"
        request.POST = QueryDict(mutable=True)
        request.POST["username"] = self.staff_user.username
        request.POST["api_key"] = self.staff_user.api_key.key

        self.assertIsInstance(auth.is_authenticated(request), HttpUnauthorized)
        self.assertFalse(getattr(request, API_KEY_AUTHENTICATED_ATTR))

    def test_authentication_rejects_inactive_user(self):
        self.staff_user.is_active = False
        self.staff_user.save()
        auth = ApiKeyOrGuestAuthentication()
        request = HttpRequest()
        request.META["HTTP_AUTHORIZATION"] = self.api_key_header()

        self.assertFalse(auth.is_authenticated(request))
        self.assertFalse(getattr(request, API_KEY_AUTHENTICATED_ATTR))

    def test_guest_authentication_ignores_existing_session_user(self):
        auth = ApiKeyOrGuestAuthentication()
        request = HttpRequest()
        request.user = self.staff_user

        self.assertTrue(auth.is_authenticated(request))
        self.assertFalse(request.user.is_authenticated)
        self.assertFalse(getattr(request, API_KEY_AUTHENTICATED_ATTR))
