from rest_framework.test import APITestCase

from django.urls import reverse_lazy


class LogoPlacementeAPIListTests(APITestCase):
    url = reverse_lazy("logo_placement_list")

    def test_list_logo_placement_as_expected(self):
        response = self.client.get(self.url)
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
