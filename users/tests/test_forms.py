from ..forms import UserChangeForm, UserCreationForm

from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class UsersFormsTestCase(TestCase):

    def test_user_creation_form(self):
        form = UserCreationForm({
            'username': 'username',
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
        self.assertTrue('username' in form.errors)

        # password mismatch
        form = UserCreationForm({
            'username': 'username2',
            'password1': 'password',
            'password2': 'passwordmismatch'
        })
        self.assertFalse(form.is_valid())
        self.assertTrue('password2' in form.errors)

    '''
    def test_user_change_form(self):
        user = User.objects.create_user(
            username='username',
            password='password'
        )
        form = UserChangeForm({
            'username': 'username2',
            'last_login': user.last_login,
            'date_joined': user.date_joined
        }, instance=user)
        self.assertTrue(form.is_valid())
        user = form.save()
        user = User.objects.get(pk=user.pk)
        self.assertEqual(user.username, 'username2')
    '''
