from model_bakery import baker

from django.urls import reverse_lazy

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

class LogoPlacementeAPIListTests(APITestCase):
    url = reverse_lazy("logo_placement_list")

    def setUp(self):
        self.user = baker.make('users.User')
        token = Token.objects.get(user=self.user)
        self.authorization = f'Token {token.key}'

    def test_list_logo_placement_as_expected(self):
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        data = response.json()
        expected_keys = set([
            "publisher",
            "sponsor",
            "description",
            "logo",
            "start_date",
            "end_date",
            "sponsor_url",
            "flight"
        ])

        self.assertEqual(200, response.status_code)
        self.assertEqual(expected_keys, set(data[0]))

    def test_invalid_token(self):
        Token.objects.all().delete()
        response = self.client.get(self.url, HTTP_AUTHORIZATION=self.authorization)
        self.assertEqual(401, response.status_code)
