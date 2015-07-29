from ..forms import UserChangeForm, UserCreationForm

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UsersFormsTestCase(TestCase):

    def test_user_creation_form(self):
        form = UserCreationForm({
            'username': 'username',
            'email': 'test@example.com',
            'password1': 'password',
            'password2': 'password'
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.username, 'username')
        logged_in = self.client.login(username=user.username, password='password')
        self.assertTrue(logged_in)

        # dupe username
        form = UserCreationForm({
            'username': 'username',
            'password1': 'password',
            'password2': 'password'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

        # password mismatch
        form = UserCreationForm({
            'username': 'username2',
            'password1': 'password',
            'password2': 'passwordmismatch'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_duplicate_email(self):
        User.objects.create_user('test1', 'test@example.com', 'testpass')

        # dupe email
        form = UserCreationForm({
            'username': 'username2',
            'email': 'test@example.com',
            'password1': 'password',
            'password2': 'password'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
