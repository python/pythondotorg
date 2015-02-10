from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from users.factories import UserFactory


@override_settings(DEBUG=True)
class ViewTests(TestCase):

    def test_devfixture(self):
        url = reverse('pydotorg-devfixture')
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

    def test_admin_docs(self):
        url = reverse('django-admindocs-tags')

        staff_user = UserFactory.create()
        staff_user.is_staff = True
        staff_user.set_password('password')
        staff_user.save()

        self.client.login(username=staff_user.username, password='password')

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        self.client.logout()
