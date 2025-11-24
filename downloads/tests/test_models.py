from ..models import Release, ReleaseFile
from .base import BaseDownloadTests


class DownloadModelTests(BaseDownloadTests):

    def test_stringification(self):
        self.assertEqual(str(self.osx), 'macOS')
        self.assertEqual(str(self.release_275), 'Python 2.7.5')

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

    def test_get_version(self):
        self.assertEqual(self.release_275.name, 'Python 2.7.5')
        self.assertEqual(self.release_275.get_version(), '2.7.5')

    def test_get_version_27(self):
        release = Release.objects.create(name='Python 2.7.12')
        self.assertEqual(release.name, 'Python 2.7.12')
        self.assertEqual(release.get_version(), '2.7.12')

    def test_get_version_invalid(self):
        names = [
            'spam', 'Python2.7.5', 'Python   2.7.7', r'Python\t2.7.9',
            r'\tPython 2.8.0',
        ]
        for name in names:
            with self.subTest(name=name):
                release = Release.objects.create(name=name)
                self.assertEqual(release.name, name)
                self.assertEqual(release.get_version(), "")

    def test_is_version_at_least(self):
        self.assertFalse(self.release_275.is_version_at_least_3_5)
        self.assertFalse(self.release_275.is_version_at_least_3_9)

        release_38 = Release.objects.create(name='Python 3.8.0')
        self.assertFalse(release_38.is_version_at_least_3_9)
        self.assertTrue(release_38.is_version_at_least_3_5)

        release_310 = Release.objects.create(name='Python 3.10.0')
        self.assertTrue(release_310.is_version_at_least_3_9)
        self.assertTrue(release_310.is_version_at_least_3_5)

    def test_is_version_at_least_with_invalid_name(self):
        """Test that is_version_at_least returns False for releases with invalid names"""
        invalid_release = Release.objects.create(name='Python install manager')
        # Should return False instead of raising AttributeError
        self.assertFalse(invalid_release.is_version_at_least_3_5)
        self.assertFalse(invalid_release.is_version_at_least_3_9)
        self.assertFalse(invalid_release.is_version_at_least_3_14)

    def test_update_supernav(self):
        from ..models import update_supernav
        from boxes.models import Box

        release = Release.objects.create(
            name='Python install manager 25.0',
            version=Release.PYMANAGER,
            is_latest=True,
            is_published=True,
        )

        for os, slug in [
            (self.windows, 'python3.10-windows'),
            (self.osx, 'python3.10-macos'),
            (self.linux, 'python3.10-linux'),
        ]:
            ReleaseFile.objects.create(
                os=os,
                release=self.python_3,
                slug=slug,
                name='Python 3.10',
                url='/ftp/python/{}.zip'.format(slug),
                download_button=True,
            )

        update_supernav()

        content = Box.objects.get(label='supernav-python-downloads').content.rendered
        self.assertIn('class="download-os-windows"', content)
        self.assertNotIn('pymanager-25.0.msix', content)
        self.assertIn('python3.10-windows.zip', content)
        self.assertIn('class="download-os-macos"', content)
        self.assertIn('python3.10-macos.zip', content)
        self.assertIn('class="download-os-linux"', content)
        self.assertIn('python3.10-linux.zip', content)

        ReleaseFile.objects.create(
            os=self.windows,
            release=release,
            name='MSIX',
            url='/ftp/python/pymanager/pymanager-25.0.msix',
            download_button=True,
        )

        update_supernav()

        content = Box.objects.get(label='supernav-python-downloads').content.rendered
        self.assertIn('class="download-os-windows"', content)
        self.assertIn('pymanager-25.0.msix', content)
        self.assertIn('python3.10-windows.zip', content)
