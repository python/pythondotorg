from rest_framework.test import APITestCase

from pydotorg.drf import BaseAPITestCase

from pages.factories import PageFactory
from users.factories import UserFactory


class PageApiViewsTest(BaseAPITestCase, APITestCase):
    app_label = 'pages'

    @classmethod
    def setUpTestData(cls):
        cls.page = PageFactory(keywords='python, django')
        cls.page2 = PageFactory(keywords='django')
        cls.page_unpublished = PageFactory(keywords='python', is_published=False)
        cls.staff_user = UserFactory(
            username='staffuser',
            password='passworduser',
            is_staff=True,
        )
        cls.Authorization = 'Token {}'.format(cls.staff_user.auth_token.key)

    def test_get_published_pages(self):
        url = self.create_url('page')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_get_all_pages(self):
        # Login to get all pages.
        url = self.create_url('page')
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_filter_page(self):
        url = self.create_url('page', filters={'keywords__icontains': 'PYTHON'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        # Login to filter all pages.
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        # This should return an empty result because normal users
        # cannot see unpublished pages.
        url = self.create_url('page', filters={'is_published': False})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        # This should return only unpublished pages.
        response = self.client.get(url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_post_page(self):
        url = self.create_url('page')
        data = {
            'title': 'Paradise Lost - The Longest Winter',
            'path': '/the-longest-winter/',
            'keywords': 'paradise lost, doom death metal',
            'is_published': True,
        }
        response = self.json_client('POST', url, data)
        self.assertEqual(response.status_code, 401)

        # 'PageViewSet' is read-only.
        response = self.json_client('POST', url, data, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 405)

    def test_delete_page(self):
        url = self.create_url('page', self.page.pk)
        response = self.json_client('DELETE', url)
        self.assertEqual(response.status_code, 401)

        # 'PageViewSet' is read-only.
        response = self.json_client('DELETE', url, HTTP_AUTHORIZATION=self.Authorization)
        self.assertEqual(response.status_code, 405)
