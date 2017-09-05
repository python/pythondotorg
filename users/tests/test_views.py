from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from users.factories import UserFactory

from ..factories import MembershipFactory

User = get_user_model()


class UsersViewsTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory(
            username='username',
            password='password',
            email='niklas@sundin.se',
            membership=None,
        )
        self.user2 = UserFactory(
            username='spameggs',
            password='password',
            search_visibility=User.SEARCH_PRIVATE,
            email_privacy=User.EMAIL_PRIVATE,
            public_profile=False,
        )

    def assertUserCreated(self, data=None, template_name='account/verification_sent.html'):
        post_data = {
            'username': 'guido',
            'email': 'montyopython@python.org',
            'password1': 'password',
            'password2': 'password',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        post_data.update(data or {})
        url = reverse('account_signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name)
        user = User.objects.get(username=post_data['username'])
        self.assertEqual(user.username, post_data['username'])
        self.assertEqual(user.email, post_data['email'])
        return response

    def test_membership_create(self):
        url = reverse('users:user_membership_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Requires login now

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

        self.assertTrue(self.user2.has_membership)
        self.client.login(username=self.user2, password='password')
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

    def test_membership_update_404(self):
        url = reverse('users:user_membership_edit')
        self.assertFalse(self.user.has_membership)
        self.client.login(username=self.user, password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_user_has_already_have_membership(self):
        # Should redirect to /membership/edit/ if user already
        # has membership.
        url = reverse('users:user_membership_create')
        self.assertTrue(self.user2.has_membership)
        self.client.login(username=self.user2, password='password')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('users:user_membership_edit'))

    def test_user_update(self):
        self.client.login(username='username', password='password')
        url = reverse('users:user_profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        post_data = {
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_user_update_redirect(self):
        # see issue #925
        self.client.login(username='username', password='password')
        url = reverse('users:user_profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # should return 200 if the user does want to see their user profile
        post_data = {
            'search_visibility': 0,
            'email_privacy': 1,
            'public_profile': False,
            'email': 'niklas@sundin.se',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        response = self.client.post(url, post_data)
        profile_url = reverse('users:user_detail', kwargs={'slug': 'username'})
        self.assertRedirects(response, profile_url)

        # should return 404 for another user
        another_user_url = reverse('users:user_detail', kwargs={'slug': 'spameggs'})
        response = self.client.get(another_user_url)
        self.assertEqual(response.status_code, 404)

        # should return 404 if the user is not logged-in
        self.client.logout()
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 404)

    def test_user_detail(self):
        # Ensure detail page is viewable without login, but that edit URLs
        # do not appear
        detail_url = reverse('users:user_detail', kwargs={'slug': self.user.username})
        edit_url = reverse('users:user_profile_edit')
        response = self.client.get(detail_url)
        self.assertTrue(self.user.is_active)
        self.assertNotContains(response, edit_url)

        # Ensure edit url is available to logged in users
        self.client.login(username='username', password='password')
        response = self.client.get(detail_url)
        self.assertContains(response, edit_url)

        # Ensure inactive accounts shouldn't be shown to users.
        user = User.objects.create_user(
            username='foobar',
            password='baz',
            email='paradiselost@example.com',
        )
        user.is_active = False
        user.save()
        self.assertFalse(user.is_active)
        detail_url = reverse('users:user_detail', kwargs={'slug': user.username})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 404)

    def test_special_usernames(self):
        # Ensure usernames in the forms of:
        # first.last
        # user@host.com
        # are allowed to view their profile pages since we allow them in
        # the username field
        u1 = User.objects.create_user(
            username='user.name',
            password='password',
        )
        detail_url = reverse('users:user_detail', kwargs={'slug': u1.username})
        edit_url = reverse('users:user_profile_edit')

        self.client.login(username=u1.username, password='password')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        u2 = User.objects.create_user(
            username='user@example.com',
            password='password',
        )

        detail_url = reverse('users:user_detail', kwargs={'slug': u2.username})
        edit_url = reverse('users:user_profile_edit')

        self.client.login(username=u2.username, password='password')
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

    def test_user_new_account(self):
        self.assertUserCreated(data={
            'username': 'thisusernamedoesntexist',
            'email': 'thereisnoemail@likesthis.com',
            'password1': 'password',
            'password2': 'password',
        })

    def test_user_duplicate_username_email(self):
        post_data = {
            'username': 'thisusernamedoesntexist',
            'email': 'thereisnoemail@likesthis.com',
            'password1': 'password',
            'password2': 'password',
        }
        self.assertUserCreated(data=post_data)
        response = self.assertUserCreated(
            data=post_data, template_name='account/signup.html'
        )
        self.assertContains(
            response, 'A user with that username already exists.'
        )
        self.assertContains(
            response, 'A user is already registered with this e-mail address.'
        )

    def test_usernames(self):
        url = reverse('account_signup')
        usernames = [
            'foaso+bar', 'foo.barahgs', 'foo@barbazbaz',
            'foo.baarBAZ',
        ]
        post_data = {
            'username': 'thisusernamedoesntexist',
            'email': 'thereisnoemail@likesthis.com',
            'password1': 'password',
            'password2': 'password',
            settings.HONEYPOT_FIELD_NAME: settings.HONEYPOT_VALUE,
        }
        for i, username in enumerate(usernames):
            with self.subTest(i=i, username=username):
                post_data.update({
                    'username': username,
                    'email': 'foo{}@example.com'.format(i)
                })
                response = self.client.post(url, post_data, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, 'account/verification_sent.html')

    def test_is_active_login(self):
        # 'allauth.account.auth_backends.AuthenticationBackend'
        # doesn't reject inactive users (but
        # 'django.contrib.auth.backends.ModelBackend' does since
        # Django 1.10) so if we use 'self.client.login()' it will
        # return True. The actual rejection performs by the
        # 'perform_login()' helper and it redirects inactive users
        # to a separate view.
        url = reverse('account_login')
        user = UserFactory(is_active=False)
        data = {'login': user.username, 'password': 'password'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('account_inactive'))
        url = reverse('users:user_membership_create')
        response = self.client.get(url)
        # Ensure that an inactive user didn't get logged in.
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('account_login'), url)
        )

    def test_user_list(self):
        url = reverse('users:user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['user_list']), 1)
