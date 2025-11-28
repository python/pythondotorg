import unittest.mock as mock

import requests
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from ..templatetags.download_tags import get_eol_info, get_python_releases_data
from .base import BaseDownloadTests

MOCK_PYTHON_RELEASE = {
    "metadata": {
        "2.7": {"status": "end-of-life", "end_of_life": "2020-01-01"},
        "3.8": {"status": "end-of-life", "end_of_life": "2024-10-07"},
        "3.10": {"status": "security", "end_of_life": "2026-10-04"},
    }
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

    @mock.patch("downloads.templatetags.download_tags.get_python_releases_data")
    def test_eol_status(self, mock_get_data):
        """Test get_eol_info returns correct EOL status."""
        # Arrange
        mock_get_data.return_value = MOCK_PYTHON_RELEASE
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

    @mock.patch("downloads.templatetags.download_tags.get_python_releases_data")
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

    @mock.patch("downloads.templatetags.download_tags.requests.get")
    def test_successful_fetch(self, mock_get):
        """Test successful API fetch."""
        # Arrange
        mock_response = mock.Mock()
        mock_response.json.return_value = MOCK_PYTHON_RELEASE
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        # Act
        result = get_python_releases_data()

        # Assert
        self.assertEqual(result, MOCK_PYTHON_RELEASE)
        mock_get.assert_called_once()

    @mock.patch("downloads.templatetags.download_tags.requests.get")
    def test_caches_result(self, mock_get):
        """Test that the result is cached."""
        # Arrange
        mock_response = mock.Mock()
        mock_response.json.return_value = MOCK_PYTHON_RELEASE
        mock_response.raise_for_status = mock.Mock()
        mock_get.return_value = mock_response

        # Act
        result1 = get_python_releases_data()
        result2 = get_python_releases_data()

        # Assert
        self.assertEqual(result1, result2)
        mock_get.assert_called_once()

    @mock.patch("downloads.templatetags.download_tags.requests.get")
    def test_request_exception_returns_none(self, mock_get):
        """Test that request exceptions return None."""
        # Arrange
        mock_get.side_effect = requests.RequestException("Connection error")

        # Act
        result = get_python_releases_data()

        # Assert
        self.assertIsNone(result)

    @mock.patch("downloads.templatetags.download_tags.requests.get")
    def test_json_decode_error_returns_none(self, mock_get):
        """Test that JSON decode errors return None."""
        # Arrange
        mock_response = mock.Mock()
        mock_response.raise_for_status = mock.Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        # Act
        result = get_python_releases_data()

        # Assert
        self.assertIsNone(result)


@override_settings(CACHES=TEST_CACHES)
class EOLBannerViewTests(BaseDownloadTests):

    def setUp(self):
        super().setUp()
        cache.clear()

    @mock.patch("downloads.templatetags.download_tags.get_python_releases_data")
    def test_eol_banner_visibility(self, mock_get_data):
        """Test EOL banner is shown or hidden correctly."""
        # Arrange
        tests = [
            ("release_275", MOCK_PYTHON_RELEASE, True),
            ("python_3_8_20", MOCK_PYTHON_RELEASE, True),
            ("python_3_10_18", MOCK_PYTHON_RELEASE, False),
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
