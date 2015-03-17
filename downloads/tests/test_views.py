from .base import BaseDownloadTests

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from ..models import OS, Release
from pages.models import Page

import json

User = get_user_model()


class DownloadViewsTests(BaseDownloadTests):
    def test_download_full_os_list(self):
        url = reverse('download:download_full_os_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download_release_detail(self):
        url = reverse('download:download_release_detail', kwargs={'release_slug': self.release_275.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        url = reverse('download:download_release_detail', kwargs={'release_slug': 'fake_slug'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_download_os_list(self):
        url = reverse('download:download_os_list', kwargs={'slug': self.linux.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_download(self):
        url = reverse('download:download')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


    def test_latest_redirects(self):
        latest_python2 = Release.objects.released().python2().latest()
        url = reverse('download:download_latest_python2')
        response = self.client.get(url)
        self.assertRedirects(response, latest_python2.get_absolute_url())

        latest_python3 = Release.objects.released().python3().latest()
        url = reverse('download:download_latest_python3')
        response = self.client.get(url)
        self.assertRedirects(response, latest_python3.get_absolute_url())


class DownloadApiViewsTest(BaseDownloadTests):
    def setUp(self):
        super().setUp()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='passworduser',
        )
        self.staff_user.is_staff = True
        self.staff_user.save()
        self.staff_key = self.staff_user.api_key.key
        self.Authorization = "ApiKey %s:%s" % (self.staff_user.username, self.staff_key)

    def json_client(self, method, url, data=None, **headers):
        if not data:
            data = {}
        client_method = getattr(self.client, method.lower())
        return client_method(url, json.dumps(data), content_type='application/json', **headers)

    def test_get_os(self):
        url = '/api/v1/downloads/os/'
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_os(self):
        url = '/api/v1/downloads/os/'
        data = {
            'name': 'BeOS',
            'slug': 'beos',
        }

        self.client.logout()
        response = self.json_client('post', url, data)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('post', url, data, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

    def test_delete_os(self):
        url = '/api/v1/downloads/os/%d/' % OS.objects.all()[0].pk

        self.client.logout()
        response = self.json_client('delete', url)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('delete', url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

    def test_get_release(self):
        url = '/api/v1/downloads/release/'
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_post_release(self):
        release_page = Page.objects.create(
            title='python 3.3',
            path='/rels/3-3/',
            content='python 3.3. released'
        )
        url = '/api/v1/downloads/release/'
        data = {
            'name': 'python 3.3',
            'slug': 'py3-3',
            'release_page': '/api/v1/pages/page/%d/' % release_page.pk
        }

        self.client.logout()
        response = self.json_client('post', url, data)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('post', url, data, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)
