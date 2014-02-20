from .base import BaseDownloadTests

from django.core.urlresolvers import reverse


class DownloadModelTests(BaseDownloadTests):
    def test_download_full_os_list(self):
        url = reverse('download:download_full_os_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_release_detail(self):
        url = reverse('download:download_release_detail', kwargs={'release_slug': self.release_275.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_os_list(self):
        url = reverse('download:download_os_list', kwargs={'slug': self.linux.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download(self):
        url = reverse('download:download')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
