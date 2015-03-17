from ..models import Release
from .base import BaseDownloadTests


class DownloadModelTests(BaseDownloadTests):

    def test_stringification(self):
        self.assertEqual(str(self.osx), 'Mac OSX')
        self.assertEqual(str(self.release_275), 'Python 2.7.5')

    def test_published(self):
        published_releases = Release.objects.published()
        self.assertEqual(len(published_releases), 4)
        self.assertTrue(self.release_275 in published_releases)
        self.assertTrue(self.hidden_release in published_releases)
        self.assertFalse(self.draft_release in published_releases)

    def test_release(self):
        released_versions = Release.objects.released()
        self.assertEqual(len(released_versions), 3)
        self.assertTrue(self.release_275 in released_versions)
        self.assertTrue(self.hidden_release in released_versions)
        self.assertFalse(self.draft_release in released_versions)
        self.assertFalse(self.pre_release in released_versions)

    def test_pre_release(self):
        pre_release_versions = Release.objects.pre_release()
        self.assertEqual(len(pre_release_versions), 1)
        self.assertTrue(self.pre_release in pre_release_versions)

    def test_draft(self):
        draft_releases = Release.objects.draft()
        self.assertEqual(len(draft_releases), 1)
        self.assertFalse(self.release_275 in draft_releases)
        self.assertFalse(self.hidden_release in draft_releases)
        self.assertTrue(self.draft_release in draft_releases)

    def test_downloads(self):
        downloads = Release.objects.downloads()
        self.assertEqual(len(downloads), 3)
        self.assertTrue(self.release_275 in downloads)
        self.assertFalse(self.hidden_release in downloads)
        self.assertFalse(self.draft_release in downloads)

    def test_python2(self):
        versions = Release.objects.python2()
        self.assertEqual(len(versions), 1)
        self.assertTrue(self.release_275 in versions)

    def test_python3(self):
        versions = Release.objects.python3()
        self.assertEqual(len(versions), 3)
        self.assertFalse(self.release_275 in versions)
        self.assertFalse(self.draft_release in versions)
        self.assertTrue(self.hidden_release in versions)
        self.assertTrue(self.pre_release in versions)
