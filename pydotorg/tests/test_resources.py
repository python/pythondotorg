from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.test import TestCase
from tastypie.http import HttpUnauthorized

from pydotorg.resources import ApiKeyOrGuestAuthentication

User = get_user_model()


class TestResources(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="passworduser",
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

    def test_authentication(self):
        request = HttpRequest()
        auth = ApiKeyOrGuestAuthentication()
        self.assertTrue(auth.is_authenticated(request))

        request.GET["username"] = self.staff_user.username
        self.assertTrue(auth.is_authenticated(request))

        request.GET["api_key"] = self.staff_user.api_key.key
        self.assertTrue(auth.is_authenticated(request))

    def test_authentication_staff_unauthorized(self):
        auth = ApiKeyOrGuestAuthentication()

        request = HttpRequest()
        request.GET["username"] = self.staff_user.username
        request.GET["api_key"] = "not-api-key"
        self.assertIsInstance(auth.is_authenticated(request), HttpUnauthorized)

        request = HttpRequest()
        request.GET["username"] = "not-staff"
        request.GET["api_key"] = self.staff_user.api_key.key
        self.assertIsInstance(auth.is_authenticated(request), HttpUnauthorized)
