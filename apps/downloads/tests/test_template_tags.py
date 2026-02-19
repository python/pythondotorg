from unittest import mock

import requests
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.downloads.templatetags.download_tags import get_eol_info, get_release_cycle_data, render_active_releases
from apps.downloads.tests.base import BaseDownloadTests

MOCK_RELEASE_CYCLE = {
    "2.7": {"status": "end-of-life", "end_of_life": "2020-01-01", "pep": 373},
    "3.8": {"status": "end-of-life", "end_of_life": "2024-10-07", "pep": 569},
    "3.9": {"status": "end-of-life", "end_of_life": "2025-10-31", "pep": 596},
    "3.10": {"status": "security", "end_of_life": "2026-10-04", "pep": 619},
    "3.14": {"status": "bugfix", "first_release": "2025-10-07", "end_of_life": "2030-10", "pep": 745},
    "3.15": {"status": "feature", "first_release": "2026-10-01", "end_of_life": "2031-10", "pep": 790},
}


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}


@override_settings(CACHES=TEST_CACHES)
class GetEOLInfoTests(BaseDownloadTests):
    def setUp(self):
        super().setUp()
        cache.clear()

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_eol_status(self, mock_get_data):
        """Test get_eol_info returns correct EOL status."""
        # Arrange
        mock_get_data.return_value = MOCK_RELEASE_CYCLE
        tests = [
            (self.release_275, True, "2020-01-01"),  # EOL
            (self.python_3_8_20, True, "2024-10-07"),  # EOL
            (self.python_3_10_18, False, None),  # security
        ]

        for release, expected_is_eol, expected_eol_date in tests:
            with self.subTest(release=release.name):
                # Act
                result = get_eol_info(release)

                # Assert
                self.assertEqual(result["is_eol"], expected_is_eol)
                self.assertEqual(result["eol_date"], expected_eol_date)

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_eol_status_api_failure(self, mock_get_data):
        """Test that API failure results in not showing EOL warning."""
        # Arrange
        mock_get_data.return_value = None

        # Act
        result = get_eol_info(self.python_3_8_20)

        # Assert
        self.assertFalse(result["is_eol"])
        self.assertIsNone(result["eol_date"])


@override_settings(CACHES=TEST_CACHES)
class GetReleaseCycleDataTests(TestCase):
    def setUp(self):
        cache.clear()

    @mock.patch("apps.downloads.templatetags.download_tags.requests.get")
    def test_successful_fetch(self, mock_get):
        """Test successful API fetch."""
        # Arrange
        mock_response = mock.Mock()
        mock_response.json.return_value = MOCK_RELEASE_CYCLE
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        # Act
        result = get_release_cycle_data()

        # Assert
        self.assertEqual(result, MOCK_RELEASE_CYCLE)
        mock_get.assert_called_once()

    @mock.patch("apps.downloads.templatetags.download_tags.requests.get")
    def test_caches_result(self, mock_get):
        """Test that the result is cached."""
        # Arrange
        mock_response = mock.Mock()
        mock_response.json.return_value = MOCK_RELEASE_CYCLE
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        # Act
        result1 = get_release_cycle_data()
        result2 = get_release_cycle_data()

        # Assert
        self.assertEqual(result1, result2)
        mock_get.assert_called_once()

    @mock.patch("apps.downloads.templatetags.download_tags.requests.get")
    def test_request_exception_returns_none(self, mock_get):
        """Test that request exceptions return None."""
        # Arrange
        mock_get.side_effect = requests.RequestException("Connection error")

        # Act
        result = get_release_cycle_data()

        # Assert
        self.assertIsNone(result)

    @mock.patch("apps.downloads.templatetags.download_tags.requests.get")
    def test_json_decode_error_returns_none(self, mock_get):
        """Test that JSON decode errors return None."""
        # Arrange
        mock_response = mock.Mock()
        mock_response.raise_for_status = mock.Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        # Act
        result = get_release_cycle_data()

        # Assert
        self.assertIsNone(result)


@override_settings(CACHES=TEST_CACHES)
class EOLBannerViewTests(BaseDownloadTests):
    def setUp(self):
        super().setUp()
        cache.clear()

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_eol_banner_visibility(self, mock_get_data):
        """Test EOL banner is shown or hidden correctly."""
        # Arrange
        tests = [
            ("release_275", MOCK_RELEASE_CYCLE, True),
            ("python_3_8_20", MOCK_RELEASE_CYCLE, True),
            ("python_3_10_18", MOCK_RELEASE_CYCLE, False),
            ("python_3_8_20", None, False),
        ]

        for release_attr, mock_data, expect_banner in tests:
            with self.subTest(release=release_attr):
                mock_get_data.return_value = mock_data
                release = getattr(self, release_attr)
                url = reverse(
                    "download:download_release_detail",
                    kwargs={"release_slug": release.slug},
                )

                # Act
                response = self.client.get(url)

                # Assert
                self.assertEqual(response.status_code, 200)
                if expect_banner:
                    self.assertContains(response, "level-error")
                    self.assertContains(response, "no longer supported")
                else:
                    self.assertNotContains(response, "level-error")


@override_settings(CACHES=TEST_CACHES)
class RenderActiveReleasesTests(BaseDownloadTests):
    def setUp(self):
        super().setUp()
        cache.clear()

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_versions_sorted_descending(self, mock_get_data):
        """Test that versions are sorted in descending order."""
        mock_get_data.return_value = MOCK_RELEASE_CYCLE

        result = render_active_releases()

        versions = [r["version"] for r in result["releases"]]
        # 3.15, 3.14, 3.10, 3.9 (first EOL); 3.8 and 2.7 skipped (older EOL)
        self.assertEqual(versions, ["3.15", "3.14", "3.10", "3.9"])

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_feature_status_becomes_prerelease(self, mock_get_data):
        """Test that 'feature' status is converted to 'pre-release'."""
        mock_get_data.return_value = MOCK_RELEASE_CYCLE

        result = render_active_releases()

        prerelease = result["releases"][0]
        self.assertEqual(prerelease["version"], "3.15")
        self.assertEqual(prerelease["status"], "pre-release")

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_feature_first_release_shows_planned(self, mock_get_data):
        """Test that feature releases show (planned) in first_release."""
        mock_get_data.return_value = MOCK_RELEASE_CYCLE

        result = render_active_releases()

        prerelease = result["releases"][0]
        self.assertEqual(prerelease["first_release"], "2026-10-01 (planned)")

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_only_one_eol_release_included(self, mock_get_data):
        """Test that only the most recent EOL release is included."""
        mock_get_data.return_value = MOCK_RELEASE_CYCLE

        result = render_active_releases()

        versions = [r["version"] for r in result["releases"]]
        # 3.9 is included (most recent EOL), 3.8 and 2.7 are not
        self.assertIn("3.9", versions)
        self.assertNotIn("3.8", versions)
        self.assertNotIn("2.7", versions)

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_eol_status_includes_last_release_link(self, mock_get_data):
        """Test that EOL status includes last release link."""
        mock_get_data.return_value = MOCK_RELEASE_CYCLE

        result = render_active_releases()

        eol_release = next(r for r in result["releases"] if r["version"] == "3.9")
        status = str(eol_release["status"])
        self.assertIn("end-of-life", status)
        self.assertIn("last release was", status)
        self.assertIn("<a href=", status)

    @mock.patch("apps.downloads.templatetags.download_tags.get_release_cycle_data")
    def test_api_failure_returns_empty_releases(self, mock_get_data):
        """Test that API failure returns empty releases list."""
        mock_get_data.return_value = None

        result = render_active_releases()

        self.assertEqual(result["releases"], [])
