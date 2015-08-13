from django.contrib.auth import get_user_model
from django.test import TestCase

from allauth.account.forms import SignupForm

User = get_user_model()


class UsersFormsTestCase(TestCase):

    def test_signup_form(self):
        form = SignupForm({
            'username': 'username',
            'email': 'test@example.com',
            'password1': 'password',
            'password2': 'password'
        })
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        form = SignupForm({
            'username': 'username2',
            'email': 'test@example.com',
            'password1': 'password',
            'password2': 'passwordmismatch'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn(
            'You must type the same password each time.',
            form.errors['__all__']
        )

    def test_duplicate_username(self):
        User.objects.create_user('username2', 'test@example.com', 'testpass')

        form = SignupForm({
            'username': 'username2',
            'email': 'test2@example.com',
            'password1': 'password',
            'password2': 'password'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_duplicate_email(self):
        User.objects.create_user('test1', 'test@example.com', 'testpass')

        form = SignupForm({
            'username': 'username2',
            'email': 'test@example.com',
            'password1': 'password',
            'password2': 'password'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
