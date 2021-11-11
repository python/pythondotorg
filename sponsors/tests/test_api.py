from django.contrib.auth.models import Permission
from django.urls import reverse_lazy
from django.utils.text import slugify
from model_bakery import baker
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from sponsors.models import Sponsor
from sponsors.models.enums import LogoPlacementChoices, PublisherChoices


class LogoPlacementeAPIListTests(APITestCase):
    url = reverse_lazy("logo_placement_list")

    def setUp(self):
        self.user = baker.make('users.User')
        token = Token.objects.get(user=self.user)
        self.permission = Permission.objects.get(name='Can access sponsor placement API')
        self.user.user_permissions.add(self.permission)
        self.authorization = f'Token {token.key}'
        self.sponsors = baker.make(Sponsor, _create_files=True, _quantity=3)

    def tearDown(self):
        for sponsor in Sponsor.objects.all():
            if sponsor.web_logo:
                sponsor.web_logo.delete()
            if sponsor.print_logo:
                sponsor.print_logo.delete()

    def test_list_logo_placement_as_expected(self):
        sp1, sp2, sp3 = baker.make_recipe("sponsors.tests.finalized_sponsorship", sponsor=iter(self.sponsors), _quantity=3)
        baker.make_recipe("sponsors.tests.logo_at_download_feature", sponsor_benefit__sponsorship=sp1)
        baker.make_recipe("sponsors.tests.logo_at_sponsors_feature", sponsor_benefit__sponsorship=sp1)
        baker.make_recipe("sponsors.tests.logo_at_sponsors_feature", sponsor_benefit__sponsorship=sp2)
        baker.make_recipe("sponsors.tests.logo_at_pypi_feature", sponsor_benefit__sponsorship=sp3, link_to_sponsors_page=True, describe_as_sponsor=True)

        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        data = response.json()

        self.assertEqual(200, response.status_code)
        self.assertEqual(4, len(data))
        self.assertEqual(2, len([p for p in data if p["flight"] == LogoPlacementChoices.SPONSORS_PAGE.value]))
        self.assertEqual(1, len([p for p in data if p["flight"] == LogoPlacementChoices.DOWNLOAD_PAGE.value]))
        self.assertEqual(1, len([p for p in data if p["flight"] == LogoPlacementChoices.SIDEBAR.value]))
        self.assertEqual(2, len([p for p in data if p["sponsor"] == self.sponsors[0].name]))
        self.assertEqual(1, len([p for p in data if p["sponsor"] == self.sponsors[1].name]))
        self.assertEqual(1, len([p for p in data if p["sponsor"] == self.sponsors[2].name]))
        self.assertEqual(
            None,
            [p for p in data if p["publisher"] == PublisherChoices.FOUNDATION.value][0]['sponsor_url']
        )
        self.assertEqual(
            f"http://testserver/psf/sponsors/#{slugify(sp3.sponsor.name)}",
            [p for p in data if p["publisher"] == PublisherChoices.PYPI.value][0]['sponsor_url']
        )
        self.assertEqual(
            sp1.sponsor.description,
            [p for p in data if p["publisher"] == PublisherChoices.FOUNDATION.value][0]['description']
        )
        self.assertEqual(
            f"{sp3.sponsor.name} is a {sp3.level_name} sponsor of the Python Software Foundation.",
            [p for p in data if p["publisher"] == PublisherChoices.PYPI.value][0]['description']
        )

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
