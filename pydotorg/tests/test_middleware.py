from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings

from pydotorg.middleware import GlobalSurrogateKey


class MiddlewareTests(TestCase):
    def test_admin_caching(self):
        """Ensure admin is not cached"""
        response = self.client.get("/admin/")
        self.assertTrue(response.has_header("Cache-Control"))
        self.assertEqual(response["Cache-Control"], "private")

    def test_redirects(self):
        """
        More of a sanity check just in case some other middleware interferes.
        """
        redirect = Redirect.objects.create(
            old_path="/old_path/", new_path="http://redirected.example.com", site=Site.objects.get_current()
        )
        url = redirect.old_path
        response = self.client.get(url)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], redirect.new_path)


class GlobalSurrogateKeyTests(TestCase):
    def test_get_section_key(self):
        """Test section key extraction from URL paths."""
        middleware = GlobalSurrogateKey(lambda r: None)

        self.assertEqual(middleware._get_section_key("/downloads/"), "downloads")
        self.assertEqual(middleware._get_section_key("/downloads/release/python-3141/"), "downloads")
        self.assertEqual(middleware._get_section_key("/events/"), "events")
        self.assertEqual(middleware._get_section_key("/events/python-events/123/"), "events")
        self.assertEqual(middleware._get_section_key("/sponsors/"), "sponsors")

        #  returns None
        self.assertIsNone(middleware._get_section_key("/"))

        self.assertEqual(middleware._get_section_key("/downloads"), "downloads")
        self.assertEqual(middleware._get_section_key("downloads/"), "downloads")

    @override_settings(GLOBAL_SURROGATE_KEY="pydotorg-app")
    def test_surrogate_key_header_includes_section(self):
        """Test that Surrogate-Key header includes both global and section keys."""
        response = self.client.get("/downloads/")
        self.assertTrue(response.has_header("Surrogate-Key"))
        surrogate_key = response["Surrogate-Key"]

        self.assertIn("pydotorg-app", surrogate_key)
        self.assertIn("downloads", surrogate_key)

    @override_settings(GLOBAL_SURROGATE_KEY="pydotorg-app")
    def test_surrogate_key_header_homepage(self):
        """Test that homepage only has global surrogate key."""
        response = self.client.get("/")
        self.assertTrue(response.has_header("Surrogate-Key"))
        surrogate_key = response["Surrogate-Key"]
        self.assertIn("pydotorg-app", surrogate_key)
