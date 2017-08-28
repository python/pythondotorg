import unittest.mock as mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from rest_framework.test import APITestCase

from .base import BaseDownloadTests, DownloadMixin
from ..models import OS, Release
from pages.factories import PageFactory
from pydotorg.drf import BaseAPITestCase
from users.factories import UserFactory

User = get_user_model()

# We need to activate caching for throttling tests.
TEST_CACHES = dict(settings.CACHES)
TEST_CACHES['default'] = {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
}
# Note that we can't override 'REST_FRAMEWORK' with 'override_settings'
# because of https://github.com/encode/django-rest-framework/issues/2466.
TEST_THROTTLE_RATES = {
    'anon': '1/day',
    'user': '2/day',
}


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


class BaseDownloadApiViewsTest(BaseAPITestCase):
    # This API used by add-to-pydotorg.py in python/release-tools.
    app_label = 'downloads'

    def setUp(self):
        super().setUp()
        self.staff_user = UserFactory(
            username='staffuser',
            password='passworduser',
            is_staff=True,
        )
        self.staff_key = self.staff_user.api_key.key
        self.token_header = 'ApiKey'
        self.Authorization = '%s %s:%s' % (
            self.token_header, self.staff_user.username, self.staff_key,
        )
        self.Authorization_invalid = '%s invalid:token' % self.token_header

    def get_json(self, response):
        json_response = response.json()
        if 'objects' in json_response:
            return json_response['objects']
        return json_response

    def test_invalid_token(self):
        url = self.create_url('os', self.linux.pk)
        response = self.json_client(
            'delete', url, HTTP_AUTHORIZATION=self.Authorization_invalid,
        )
        self.assertEqual(response.status_code, 401)

        url = self.create_url('os')
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization_invalid)
        # TODO: API v1 returns 200 for a GET request even if token is invalid.
        # 'StaffAuthorization.read_list` returns 'object_list' unconditionally,
        # and 'StaffAuthorization.read_detail` returns 'True'.
        self.assertIn(response.status_code, [200, 401])

    def test_get_os(self):
        response = self.client.get(self.create_url('os'))
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 3)
        self.assertIn(
            self.create_url('os', self.linux.pk),
            content[0]['resource_uri']
        )
        self.assertEqual(content[0]['name'], self.linux.name)
        self.assertEqual(content[0]['slug'], self.linux.slug)
        # The following fields won't show up in the response
        # because there is no 'User' relation defined in the API.
        # See 'ReleaseResource.release_page' for an example.
        self.assertNotIn('creator', content[0])
        self.assertNotIn('last_modified_by', content[0])

    def test_post_os(self):
        url = self.create_url('os')
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
        content = self.get_json(response)
        self.assertEqual(content['name'], data['name'])
        self.assertEqual(content['slug'], data['slug'])

    def test_delete_os(self):
        url = self.create_url('os', self.linux.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertIn(url, content['resource_uri'])
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
        response = self.client.get(self.create_url('os', filters=filters))
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]['name'], self.linux.name)
        self.assertEqual(content[0]['slug'], self.linux.slug)

        response = self.client.get(self.create_url('os', filters={'name': 'invalid'}))
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 0)

        # To test 'exact' filtering in 'OSResource.Meta.filtering'.
        response = self.client.get(self.create_url('os', filters={'name': 'linu'}))
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 0)

        # Test uppercase 'self.linux.name'.
        response = self.client.get(self.create_url('os', filters={'name': self.linux.name.upper()}))
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 0)

    def test_get_release(self):
        url = self.create_url('release')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        # 'self.draft_release' won't shown here.
        self.assertEqual(len(content), 4)

        # Login to get all releases.
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 5)

    def test_post_release(self):
        release_page = PageFactory(
            title='python 3.3',
            path='/rels/3-3/',
            content='python 3.3. released'
        )
        release_page_url = self.create_url('page', release_page.pk, app_label='pages')
        response = self.client.get(release_page_url)
        self.assertEqual(response.status_code, 200)

        url = self.create_url('release')
        data = {
            'name': 'python 3.3',
            'slug': 'py3-3',
            'release_page': release_page_url,
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
        # TODO: API v1 returns 401; and API v2 returns 404.
        self.assertIn(response.status_code, [401, 404])
        response = self.client.get(new_url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(content['name'], data['name'])
        self.assertEqual(content['slug'], data['slug'])
        self.assertIn(data['release_page'], content['release_page'])

    def test_delete_release(self):
        url = self.create_url('release', self.release_275.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertIn(url, content['resource_uri'])
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
        response = self.client.get(self.create_url('release', filters={'pre_release': True}))
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 1)
        self.assertIn(
            self.create_url('release', self.pre_release.pk),
            content[0]['resource_uri']
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

    def test_get_release_file(self):
        url = self.create_url('release_file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 5)

        url = self.create_url('release_file', self.release_275_linux.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(content['name'], self.release_275_linux.name)

        url = self.create_url('release_file', 9999999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_post_release_file(self):
        url = self.create_url('release_file')
        data = {
            'name': 'File name',
            'slug': 'file-name',
            'os': self.create_url('os', self.linux.pk),
            'release': self.create_url('release', self.release_275.pk),
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
        content = self.get_json(response)
        self.assertEqual(content['name'], data['name'])
        self.assertEqual(content['slug'], data['slug'])
        # 'gpg_signature_file' is optional.
        self.assertEqual(content['gpg_signature_file'], '')
        self.assertTrue(content['is_source'])
        self.assertTrue(content['download_button'])
        self.assertIn(data['os'], content['os'])
        self.assertIn(data['release'], content['release'])
        self.assertEqual(content['description'], data['description'])

    def test_delete_release_file(self):
        url = self.create_url('release_file', self.release_275_linux.pk)
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
            self.create_url('release_file', filters={'description': 'windows'})
        )
        self.assertEqual(response.status_code, 400)
        content = self.get_json(response)
        self.assertIn('error', content)
        self.assertIn(
            '\'exact\' is not an allowed filter on the \'description\' field.',
            content['error']
        )

        response = self.client.get(
            self.create_url('release_file', filters={'description__contains': 'Windows'})
        )
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 2)

        response = self.client.get(
            self.create_url('release_file', filters={'name': self.release_275_linux.name})
        )
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 1)

        response = self.client.get(
            self.create_url('release_file', filters={'os': self.windows.pk})
        )
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 2)

        response = self.client.get(
            self.create_url('release_file', filters={'release': self.release_275.pk})
        )
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 4)

        # Combine two filters in one request.
        response = self.client.get(
            self.create_url(
                'release_file',
                filters={
                    'release': self.release_275.pk,
                    'os': self.linux.pk,
                }
            )
        )
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 1)

        # Files for a draft release should be shown to users.
        # TODO: We may deprecate this behavior when we drop API v1.
        response = self.client.get(
            self.create_url('release_file', filters={'release': self.draft_release.pk})
        )
        self.assertFalse(self.draft_release.is_published)
        self.assertEqual(response.status_code, 200)
        content = self.get_json(response)
        self.assertEqual(len(content), 1)


class DownloadApiV1ViewsTest(BaseDownloadApiViewsTest, BaseDownloadTests, TestCase):
    api_version = 'v1'


class DownloadApiV2ViewsTest(BaseDownloadApiViewsTest, BaseDownloadTests, APITestCase):
    api_version = 'v2'

    def setUp(self):
        super().setUp()
        self.staff_key = self.staff_user.auth_token.key
        self.token_header = 'Token'
        self.Authorization = '%s %s' % (self.token_header, self.staff_key)
        self.Authorization_invalid = '%s invalidtoken' % self.token_header

    def get_json(self, response):
        return response.data

    @override_settings(CACHES=TEST_CACHES)
    @mock.patch(
        'rest_framework.throttling.SimpleRateThrottle.THROTTLE_RATES',
        new=TEST_THROTTLE_RATES,
    )
    def test_throttling_anon(self):
        url = self.create_url('os')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Second request should return '429 TOO MANY REQUESTS'.
        url = self.create_url('os')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)

    @override_settings(CACHES=TEST_CACHES)
    @mock.patch(
        'rest_framework.throttling.SimpleRateThrottle.THROTTLE_RATES',
        new=TEST_THROTTLE_RATES,
    )
    def test_throttling_user(self):
        url = self.create_url('os')
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)

        # Second request should be okay for a user.
        url = self.create_url('os')
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)

        # Third request should return '429 TOO MANY REQUESTS'.
        url = self.create_url('os')
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 429)
