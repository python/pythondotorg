from django.contrib.auth.models import Permission
from django.urls import reverse_lazy
from model_bakery import baker
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from sponsors.models import Sponsor
from sponsors.models.enums import LogoPlacementChoices


class LogoPlacementeAPIListTests(APITestCase):
    url = reverse_lazy("logo_placement_list")

    def setUp(self):
        self.user = baker.make('users.User')
        token = Token.objects.get(user=self.user)
        self.permission = Permission.objects.get(name='Can access sponsor placement API')
        self.user.user_permissions.add(self.permission)
        self.authorization = f'Token {token.key}'
        self.sponsors = baker.make(Sponsor, _create_files=True, _quantity=2)

    def tearDown(self):
        for sponsor in Sponsor.objects.all():
            if sponsor.web_logo:
                sponsor.web_logo.delete()
            if sponsor.print_logo:
                sponsor.print_logo.delete()

    def test_list_logo_placement_as_expected(self):
        sp1, sp2 = baker.make_recipe("sponsors.tests.finalized_sponsorship", sponsor=iter(self.sponsors), _quantity=2)
        baker.make_recipe("sponsors.tests.logo_at_download_feature", sponsor_benefit__sponsorship=sp1)
        baker.make_recipe("sponsors.tests.logo_at_sponsors_feature", sponsor_benefit__sponsorship=sp1)
        baker.make_recipe("sponsors.tests.logo_at_sponsors_feature", sponsor_benefit__sponsorship=sp2)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        data = response.json()

        self.assertEqual(200, response.status_code)
        self.assertEqual(3, len(data))
        self.assertEqual(2, len([p for p in data if p["flight"] == LogoPlacementChoices.SPONSORS_PAGE.value]))
        self.assertEqual(1, len([p for p in data if p["flight"] == LogoPlacementChoices.DOWNLOAD_PAGE.value]))
        self.assertEqual(2, len([p for p in data if p["sponsor"] == self.sponsors[0].name]))
        self.assertEqual(1, len([p for p in data if p["sponsor"] == self.sponsors[1].name]))

    def test_invalid_token(self):
        Token.objects.all().delete()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        self.assertEqual(401, response.status_code)

    def test_superuser_user_have_permission_by_default(self):
        self.user.user_permissions.remove(self.permission)
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        self.assertEqual(200, response.status_code)

    def test_staff_have_permission_by_default(self):
        self.user.user_permissions.remove(self.permission)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        self.assertEqual(200, response.status_code)

    def test_user_must_have_required_permission(self):
        self.user.user_permissions.remove(self.permission)
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        self.assertEqual(403, response.status_code)
