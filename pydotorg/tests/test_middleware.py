from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.http import HttpResponse, StreamingHttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings

from pydotorg.middleware import AdminNoCaching, GlobalSurrogateKey


class MiddlewareTests(TestCase):
    def test_admin_caching(self):
        """Ensure admin is not cached"""
        response = self.client.get("/admin/")
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("max-age=0", response["Cache-Control"])

    def test_management_redirects_and_csrf_rejections_are_not_cached(self):
        client = Client(enforce_csrf_checks=True)
        responses = (
            (client.get("/sponsors/manage"), 301),
            (client.post("/sponsors/manage/sponsorships/1/lock/", {"action": "lock"}), 403),
        )
        for response, status in responses:
            with self.subTest(status=status):
                self.assertEqual(response.status_code, status)
                self.assertIn("private", response["Cache-Control"])
                self.assertIn("no-store", response["Cache-Control"])

    def test_csp_report_only_header(self):
        """CSP ships in Report-Only mode; the enforcing header must not be set."""
        response = self.client.get("/admin/")
        self.assertTrue(response.has_header("Content-Security-Policy-Report-Only"))
        self.assertFalse(response.has_header("Content-Security-Policy"))

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


class ManagementCacheTests(SimpleTestCase):
    def test_private_pages_and_streaming_downloads_cannot_be_cached(self):
        for path in (
            "/admin/",
            "/sponsors/manage",
            "/sponsors/manage?year=2026",
            "/sponsors/manage/sponsorships/export/",
            "/sponsors/manage/sponsorships/1/export-assets/",
            "/sponsors/documents/sponsors/contracts/signed/example.pdf/",
        ):
            with self.subTest(path=path):
                response = StreamingHttpResponse(iter([b"private"]), headers={"Cache-Control": "public, max-age=3600"})
                result = AdminNoCaching(lambda _, response=response: response)(RequestFactory().get(path))
                directives = {part.strip() for part in result["Cache-Control"].split(",")}
                self.assertTrue({"private", "no-store", "no-cache", "max-age=0"} <= directives)
                self.assertNotIn("public", directives)
                self.assertIn("Expires", result)
                result.close()

    def test_public_sponsor_paths_keep_their_cache_policy(self):
        for path in ("/sponsors/", "/sponsors/manage-other/", "/admin-other/"):
            with self.subTest(path=path):
                response = HttpResponse(headers={"Cache-Control": "public, max-age=3600"})
                result = AdminNoCaching(lambda _, response=response: response)(RequestFactory().get(path))
                self.assertEqual(result["Cache-Control"], "public, max-age=3600")


class GlobalSurrogateKeyTests(TestCase):
    def test_get_section_key(self):
        """Test section key extraction from URL paths."""
        middleware = GlobalSurrogateKey(lambda _: None)

        self.assertEqual(middleware.get_section_key("/downloads/"), "downloads")
        self.assertEqual(middleware.get_section_key("/downloads/release/python-3141/"), "downloads")
        self.assertEqual(middleware.get_section_key("/events/"), "events")
        self.assertEqual(middleware.get_section_key("/events/python-events/123/"), "events")
        self.assertEqual(middleware.get_section_key("/sponsors/"), "sponsors")

        # returns None
        self.assertIsNone(middleware.get_section_key("/"))

        self.assertEqual(middleware.get_section_key("/downloads"), "downloads")
        self.assertEqual(middleware.get_section_key("downloads/"), "downloads")

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
        self.assertEqual(surrogate_key, "pydotorg-app")
