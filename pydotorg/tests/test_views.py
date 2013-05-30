from django.core.urlresolvers import reverse
from django.test import TestCase


class ViewTests(TestCase):
    urls = 'pydotorg.urls'

    def test_sponsor_list(self):
        url = reverse('pydotorg-devfixture')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
