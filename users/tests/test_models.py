from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UsersModelsTestCase(TestCase):
    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username='username',
            password='password',
            is_beta_tester=True
        )
        self.assertNotEqual(user, None)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        kwargs = {
            'username': '',
            'password': 'password',
        }
        self.assertRaises(ValueError, User.objects.create_user, **kwargs)
