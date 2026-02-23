import datetime as dt
from unittest.mock import patch

from apps.downloads.models import Release, ReleaseFile
from apps.downloads.tests.base import BaseDownloadTests


class DownloadModelTests(BaseDownloadTests):
    def test_stringification(self):
        self.assertEqual(str(self.osx), "macOS")
        self.assertEqual(str(self.release_275), "Python 2.7.5")

    def test_published(self):
        published_releases = Release.objects.published()
        self.assertEqual(len(published_releases), 7)
        self.assertIn(self.release_275, published_releases)
        self.assertIn(self.hidden_release, published_releases)
        self.assertNotIn(self.draft_release, published_releases)

    def test_release(self):
        released_versions = Release.objects.released()
        self.assertEqual(len(released_versions), 6)
        self.assertIn(self.release_275, released_versions)
        self.assertIn(self.hidden_release, released_versions)
        self.assertNotIn(self.draft_release, released_versions)
        self.assertNotIn(self.pre_release, released_versions)

    def test_pre_release(self):
        pre_release_versions = Release.objects.pre_release()
        self.assertEqual(len(pre_release_versions), 1)
        self.assertIn(self.pre_release, pre_release_versions)

    def test_draft(self):
        draft_releases = Release.objects.draft()
        self.assertEqual(len(draft_releases), 1)
        self.assertNotIn(self.release_275, draft_releases)
        self.assertNotIn(self.hidden_release, draft_releases)
        self.assertIn(self.draft_release, draft_releases)

    def test_downloads(self):
        downloads = Release.objects.downloads()
        self.assertEqual(len(downloads), 5)
        self.assertIn(self.release_275, downloads)
        self.assertNotIn(self.hidden_release, downloads)
        self.assertNotIn(self.draft_release, downloads)
        self.assertNotIn(self.pre_release, downloads)

    def test_python2(self):
        versions = Release.objects.python2()
        self.assertEqual(len(versions), 1)
        self.assertIn(self.release_275, versions)

    def test_python3(self):
        versions = Release.objects.python3()
        self.assertEqual(len(versions), 6)
        self.assertNotIn(self.release_275, versions)
        self.assertNotIn(self.draft_release, versions)
        self.assertIn(self.hidden_release, versions)
        self.assertIn(self.pre_release, versions)

    def test_latest_python3(self):
        latest_3 = Release.objects.latest_python3()
        self.assertEqual(latest_3, self.python_3)
        self.assertNotEqual(latest_3, self.python_3_10_18)

        latest_3_10 = Release.objects.latest_python3(minor_version=10)
        self.assertEqual(latest_3_10, self.python_3)
        self.assertNotEqual(latest_3_10, self.python_3_10_18)

        latest_3_8 = Release.objects.latest_python3(minor_version=8)
        self.assertEqual(latest_3_8, self.python_3_8_20)
        self.assertNotEqual(latest_3_8, self.python_3_8_19)

        latest_3_99 = Release.objects.latest_python3(minor_version=99)
        self.assertIsNone(latest_3_99)

    def test_latest_prerelease(self):
        latest_prerelease = Release.objects.latest_prerelease()
        self.assertEqual(latest_prerelease, self.pre_release)

        # Create a newer prerelease with a future date
        newer_prerelease = Release.objects.create(
            version=Release.PYTHON3,
            name="Python 3.9.99",
            is_published=True,
            pre_release=True,
            release_date=self.pre_release.release_date + dt.timedelta(days=1),
        )
        latest_prerelease = Release.objects.latest_prerelease()
        self.assertEqual(latest_prerelease, newer_prerelease)
        self.assertNotEqual(latest_prerelease, self.pre_release)

    def test_latest_prerelease_when_no_prerelease(self):
        # Delete the prerelease
        self.pre_release.delete()
        latest_prerelease = Release.objects.latest_prerelease()
        self.assertIsNone(latest_prerelease)

    def test_get_version(self):
        self.assertEqual(self.release_275.name, "Python 2.7.5")
        self.assertEqual(self.release_275.get_version(), "2.7.5")

    def test_get_version_27(self):
        release = Release.objects.create(name="Python 2.7.12")
        self.assertEqual(release.name, "Python 2.7.12")
        self.assertEqual(release.get_version(), "2.7.12")

    def test_get_version_invalid(self):
        names = [
            "spam",
            "Python2.7.5",
            "Python   2.7.7",
            r"Python\t2.7.9",
            r"\tPython 2.8.0",
        ]
        for name in names:
            with self.subTest(name=name):
                release = Release.objects.create(name=name)
                self.assertEqual(release.name, name)
                self.assertEqual(release.get_version(), "")

    def test_is_version_at_least(self):
        self.assertFalse(self.release_275.is_version_at_least_3_5)
        self.assertFalse(self.release_275.is_version_at_least_3_9)

        release_38 = Release.objects.create(name="Python 3.8.0")
        self.assertFalse(release_38.is_version_at_least_3_9)
        self.assertTrue(release_38.is_version_at_least_3_5)

        release_310 = Release.objects.create(name="Python 3.10.0")
        self.assertTrue(release_310.is_version_at_least_3_9)
        self.assertTrue(release_310.is_version_at_least_3_5)

    def test_is_version_at_least_with_invalid_name(self):
        """Test that is_version_at_least returns False for releases with invalid names"""
        invalid_release = Release.objects.create(name="Python install manager")
        # Should return False instead of raising AttributeError
        self.assertFalse(invalid_release.is_version_at_least_3_5)
        self.assertFalse(invalid_release.is_version_at_least_3_9)
        self.assertFalse(invalid_release.is_version_at_least_3_14)

    def test_update_supernav(self):
        from apps.boxes.models import Box
        from apps.downloads.models import update_supernav

        release = Release.objects.create(
            name="Python install manager 25.0",
            version=Release.PYMANAGER,
            is_latest=True,
            is_published=True,
        )

        for os, slug in [
            (self.windows, "python3.10-windows"),
            (self.osx, "python3.10-macos"),
            (self.linux, "python3.10-linux"),
        ]:
            ReleaseFile.objects.create(
                os=os,
                release=self.python_3,
                slug=slug,
                name="Python 3.10",
                url=f"/ftp/python/{slug}.zip",
                download_button=True,
            )

        update_supernav()

        content = Box.objects.get(label="supernav-python-downloads").content.rendered
        self.assertIn('class="download-os-windows"', content)
        self.assertNotIn("pymanager-25.0.msix", content)
        self.assertIn("python3.10-windows.zip", content)
        self.assertIn('class="download-os-macos"', content)
        self.assertIn("python3.10-macos.zip", content)
        self.assertIn('class="download-os-linux"', content)
        self.assertIn("python3.10-linux.zip", content)

        ReleaseFile.objects.create(
            os=self.windows,
            release=release,
            name="MSIX",
            url="/ftp/python/pymanager/pymanager-25.0.msix",
            download_button=True,
        )

        update_supernav()

        content = Box.objects.get(label="supernav-python-downloads").content.rendered
        self.assertIn('class="download-os-windows"', content)
        self.assertIn("pymanager-25.0.msix", content)
        self.assertIn("python3.10-windows.zip", content)

    def test_update_supernav_skips_os_without_files(self):
        """Test that update_supernav works when an OS has no download files.

        Regression test for a bug where adding an OS (like Android) without
        any release files would cause update_supernav to silently abort,
        leaving the supernav showing outdated version information.
        """
        # Arrange
        from apps.boxes.models import Box
        from apps.downloads.models import OS, update_supernav

        # Create an OS without any release files
        OS.objects.create(name="Android", slug="android")

        # Create download files for other operating systems
        for os, slug in [
            (self.osx, "python3.10-macos"),
            (self.linux, "python3.10-linux"),
            (self.windows, "python3.10-windows"),
        ]:
            ReleaseFile.objects.create(
                os=os,
                release=self.python_3,
                slug=slug,
                name="Python 3.10",
                url=f"/ftp/python/{slug}.zip",
                download_button=True,
            )

        # Act
        update_supernav()

        # Assert: verify supernav was updated
        box = Box.objects.get(label="supernav-python-downloads")
        content = box.content.rendered

        # OSes with files should be present
        self.assertIn('class="download-os-windows"', content)
        self.assertIn('class="download-os-macos"', content)
        self.assertIn('class="download-os-linux"', content)

        # Android (no files) should not be present
        self.assertNotIn("android", content.lower())

    @patch("apps.downloads.models.update_supernav")
    @patch("apps.downloads.models.update_download_landing_sources_box")
    @patch("apps.downloads.models.update_homepage_download_box")
    def test_release_file_save_triggers_box_updates(self, mock_home, mock_sources, mock_supernav):
        """Saving a ReleaseFile on a published release should update boxes."""
        mock_supernav.reset_mock()
        mock_sources.reset_mock()
        mock_home.reset_mock()

        ReleaseFile.objects.create(
            os=self.windows,
            release=self.python_3,
            name="Windows installer",
            url="/ftp/python/3.10.19/python-3.10.19.exe",
            download_button=True,
        )

        mock_supernav.assert_called()
        mock_sources.assert_called()
        mock_home.assert_called()

    @patch("apps.downloads.models.update_supernav")
    @patch("apps.downloads.models.update_download_landing_sources_box")
    @patch("apps.downloads.models.update_homepage_download_box")
    def test_release_file_save_skips_unpublished_release(self, mock_home, mock_sources, mock_supernav):
        """Saving a ReleaseFile on a draft release should not update boxes."""
        mock_supernav.reset_mock()
        mock_sources.reset_mock()
        mock_home.reset_mock()

        ReleaseFile.objects.create(
            os=self.windows,
            release=self.draft_release,
            name="Windows installer draft",
            url="/ftp/python/9.7.2/python-9.7.2.exe",
        )

        mock_supernav.assert_not_called()
        mock_sources.assert_not_called()
        mock_home.assert_not_called()

    @patch("apps.downloads.models.update_supernav")
    @patch("apps.downloads.models.update_download_landing_sources_box")
    @patch("apps.downloads.models.update_homepage_download_box")
    def test_release_file_delete_triggers_box_updates(self, mock_home, mock_sources, mock_supernav):
        """Deleting a ReleaseFile on a published release should update boxes."""
        mock_supernav.reset_mock()
        mock_sources.reset_mock()
        mock_home.reset_mock()

        self.release_275_windows_32bit.delete()

        mock_supernav.assert_called()
        mock_sources.assert_called()
        mock_home.assert_called()
