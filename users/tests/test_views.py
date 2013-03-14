from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from .. import admin

User = get_user_model()


class UsersViewsTestCase(TestCase):
    urls = 'users.urls'

    def test_signup(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            'username': 'username',
            'password1': 'password',
            'password2': 'password'
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(username=post_data['username']).count(), 1)

        # user is supposed to be logged-in upon creation.
        # a logged-in user cannot create a new user
        response = self.client.get(url)
        self.assertFalse('form' in response.context)
