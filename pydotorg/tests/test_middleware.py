from django.test import TestCase


class MiddlewareTests(TestCase):

    def test_admin_caching(self):
        """ Ensure admin is not cached """
        response = self.client.get('/admin/')
        self.assertTrue(response.has_header('Cache-Control'))
        self.assertEqual(response['Cache-Control'], 'private')
