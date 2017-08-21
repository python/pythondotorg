import json
from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from django.utils.timezone import make_naive

from .base import BaseDownloadTests, DownloadMixin
from ..models import OS, Release
from pages.models import Page
from users.factories import UserFactory

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


class RegressionTests(DownloadMixin, TestCase):
    """These tests are for bugs found by Sentry."""

    def test_without_latest_python3_release(self):
        url = reverse('download:download')
        response = self.client.get(url)
        self.assertIsNone(response.context['latest_python2'])
        self.assertIsNone(response.context['latest_python3'])
        self.assertIsInstance(response.context['python_files'], list)
        self.assertEqual(len(response.context['python_files']), 3)


class DownloadApiViewsTest(BaseDownloadTests):
    # This API used by add-to-pydotorg.py in python/release-tools.

    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(
            username='staffuser',
            password='passworduser',
            is_staff=True,
        )
        self.staff_key = self.staff_user.api_key.key
        self.Authorization = "ApiKey %s:%s" % (self.staff_user.username, self.staff_key)

    def json_client(self, method, url, data=None, **headers):
        if not data:
            data = {}
        client_method = getattr(self.client, method.lower())
        return client_method(url, json.dumps(data), content_type='application/json', **headers)

    def create_url(self, model, filters=None):
        base_url = '/api/v1/downloads/%s/' % model
        if filters is not None:
            filters = '?' + urlencode(filters)
        return urljoin(base_url, filters)

    def test_get_os(self):
        url = '/api/v1/downloads/os/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 3)
        self.assertEqual(
            content[0]['resource_uri'], '/api/v1/downloads/os/%d/' % self.linux.pk
        )
        self.assertEqual(content[0]['name'], self.linux.name)
        self.assertEqual(content[0]['slug'], self.linux.slug)
        # The following fields won't show up in the response
        # because there is no 'User' relation defined in the API.
        # See 'ReleaseResource.release_page' for an example.
        self.assertNotIn('creator', content[0])
        self.assertNotIn('last_modified_by', content[0])

    def test_post_os(self):
        url = '/api/v1/downloads/os/'
        data = {
            'name': 'BeOS',
            'slug': 'beos',
        }
        response = self.json_client('post', url, data)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('post', url, data, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

        # Get the new created OS object via API.
        new_url = response['Location']
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())
        self.assertEqual(content['name'], data['name'])
        self.assertEqual(content['slug'], data['slug'])

    def test_delete_os(self):
        url = '/api/v1/downloads/os/%d/' % self.linux.pk
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())
        self.assertEqual(content['resource_uri'], url)
        self.assertEqual(content['name'], self.linux.name)
        self.assertEqual(content['slug'], self.linux.slug)

        response = self.json_client('delete', url)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('delete', url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        # Test that the OS doesn't exist.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_filter_os(self):
        filters = {
            'name': self.linux.name,
            'slug': self.linux.slug,
        }
        response = self.client.get(self.create_url('os', filters))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['name'], self.linux.name)
        self.assertEqual(content[0]['slug'], self.linux.slug)

        response = self.client.get(self.create_url('os', {'name': 'invalid'}))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 0)

        # To test 'exact' filtering in 'OSResource.Meta.filtering'.
        response = self.client.get(self.create_url('os', {'name': 'linu'}))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 0)

        # Test uppercase 'self.linux.name'.
        response = self.client.get(self.create_url('os', {'name': self.linux.name.upper()}))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 0)

    def test_get_release(self):
        url = '/api/v1/downloads/release/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        # 'self.draft_release' won't shown here.
        self.assertEqual(len(content), 4)

        # Login to get all releases.
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 5)

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
        response = self.json_client('post', url, data)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('post', url, data, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

        # Test that the release is created.
        new_url = response['Location']
        # We'll get 401 because the default value of
        # 'Release.is_published' is False.
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 401)
        response = self.client.get(new_url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())
        self.assertEqual(content['name'], data['name'])
        self.assertEqual(content['slug'], data['slug'])
        self.assertEqual(content['release_page'], data['release_page'])

    def test_delete_release(self):
        url = '/api/v1/downloads/release/%d/' % self.release_275.pk
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())
        self.assertEqual(content['resource_uri'], url)
        self.assertEqual(content['name'], self.release_275.name)
        self.assertEqual(content['slug'], self.release_275.slug)

        response = self.json_client('delete', url)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('delete', url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        # Test that the OS doesn't exist.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_filter_release(self):
        response = self.client.get(self.create_url('release', {'pre_release': True}))
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 1)
        self.assertEqual(
            content[0]['resource_uri'],
            '/api/v1/downloads/release/%d/' % self.pre_release.pk
        )
        self.assertEqual(content[0]['name'], self.pre_release.name)
        self.assertEqual(content[0]['slug'], self.pre_release.slug)
        self.assertTrue(content[0]['is_published'])
        self.assertTrue(content[0]['pre_release'])
        self.assertTrue(content[0]['show_on_download_page'])
        self.assertEqual(content[0]['version'], self.pre_release.version)
        self.assertEqual(
            content[0]['release_notes_url'],
            self.pre_release.release_notes_url
        )
        self.assertEqual(
            content[0]['release_date'],
            make_naive(self.pre_release.release_date).isoformat('T')
        )

    def test_get_release_file(self):
        url = '/api/v1/downloads/release_file/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 4)

        url = '/api/v1/downloads/release_file/%d/' % self.release_275_linux.pk
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())
        self.assertEqual(content['name'], self.release_275_linux.name)

        url = '/api/v1/downloads/release_file/9999999/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_release_file(self):
        url = '/api/v1/downloads/release_file/'
        data = {
            'name': 'File name',
            'slug': 'file-name',
            'os': '/api/v1/downloads/os/%d/' % self.linux.pk,
            'release': '/api/v1/downloads/release/%d/' % self.release_275.pk,
            'description': 'This is a description.',
            'is_source': True,
            'url': 'https://www.python.org/',
            'md5_sum': '098f6bcd4621d373cade4e832627b4f6',
            'filesize': len('098f6bcd4621d373cade4e832627b4f6'),
            'download_button': True,
        }
        response = self.json_client('post', url, data)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('post', url, data, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 201)

        # Test that the file is created.
        new_url = response['Location']
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())
        self.assertEqual(content['name'], data['name'])
        self.assertEqual(content['slug'], data['slug'])
        # 'gpg_signature_file' is optional.
        self.assertEqual(content['gpg_signature_file'], '')
        self.assertTrue(content['is_source'])
        self.assertTrue(content['download_button'])
        self.assertEqual(content['os'], data['os'])
        self.assertEqual(content['release'], data['release'])
        self.assertEqual(content['description'], data['description'])

    def test_delete_release_file(self):
        url = '/api/v1/downloads/release_file/%d/' % self.release_275_linux.pk
        response = self.json_client('delete', url)
        self.assertEqual(response.status_code, 401)

        response = self.json_client('delete', url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 204)

        # Test that the OS doesn't exist.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_filter_release_file(self):
        # We'll get 400 because 'exact' is not an allowed filter.
        response = self.client.get(
            self.create_url('release_file', {'description': 'windows'})
        )
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode())
        self.assertEqual(
            content['error'],
            '\'exact\' is not an allowed filter on the \'description\' field.'
        )

        response = self.client.get(
            self.create_url('release_file', {'description__contains': 'Windows'})
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 2)

        response = self.client.get(
            self.create_url('release_file', {'name': self.release_275_linux.name})
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 1)

        response = self.client.get(
            self.create_url('release_file', {'os': self.windows.pk})
        )
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode())['objects']
        self.assertEqual(len(content), 2)
