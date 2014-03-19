from django.test import TestCase

from django.contrib.sites.models import Site
from django.contrib.redirects.models import Redirect


class MiddlewareTests(TestCase):

    def test_admin_caching(self):
        """ Ensure admin is not cached """
        response = self.client.get('/admin/')
        self.assertTrue(response.has_header('Cache-Control'))
        self.assertEqual(response['Cache-Control'], 'private')

    def test_redirects(self):
        """
        More of a sanity check just in case some other middleware interferes.
        """
        redirect = Redirect.objects.create(
            old_path='/old_path/',
            new_path='http://redirected.example.com',
            site=Site.objects.get_current()
        )
        url = redirect.old_path
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], redirect.new_path)
