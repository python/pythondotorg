from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import admin
from ..factories import MembershipFactory

User = get_user_model()


class UsersViewsTestCase(TestCase):
    def test_membership_create(self):
        url = reverse('users:user_membership_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Requires login now

        user = User.objects.create_user(username='username', password='password')
        self.client.login(username='username', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'legal_name': 'Some Name',
            'preferred_name': 'Sommy',
            'email_address': 'sommy@example.com',
            'city': 'Lawrence',
            'region': 'Kansas',
            'country': 'USA',
            'postal_code': '66044',
            'psf_code_of_conduct': True,
            'psf_announcements': True,
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:user_membership_thanks'))

    def test_membership_update(self):
        url = reverse('users:user_membership_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Requires login now

        user = User.objects.create_user(username='username', password='password')
        membership = MembershipFactory(creator=user)
        self.client.login(username='username', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'legal_name': 'Some Name',
            'preferred_name': 'Sommy',
            'email_address': 'sommy@example.com',
            'city': 'Lawrence',
            'region': 'Kansas',
            'country': 'USA',
            'postal_code': '66044',
            'psf_announcements': True,
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

    def test_user_update(self):
        User.objects.create_user(username='username', password='password')
        self.client.login(username='username', password='password')
        url = reverse('users:user_profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_user_detail(self):
        # Ensure detail page is viewable without login, but that edit URLs
        # do not appear
        user = User.objects.create_user(username='username', password='password')
        detail_url = reverse('users:user_detail', kwargs={'slug': user.username})
        edit_url = reverse('users:user_profile_edit')
        response = self.client.get(detail_url)
        self.assertNotContains(response, edit_url)

        # Ensure edit url is available to logged in users
        self.client.login(username='username', password='password')
        response = self.client.get(detail_url)
        self.assertContains(response, edit_url)

