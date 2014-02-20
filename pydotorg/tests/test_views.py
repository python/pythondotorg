from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings


@override_settings(DEBUG=True)
class ViewTests(TestCase):
    urls = 'pydotorg.urls'

    def test_devfixture(self):
        url = reverse('pydotorg-devfixture')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
