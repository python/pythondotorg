from test_plus.test import TestCase

from users.factories import UserFactory, MembershipFactory
from users.models import Membership


class MembershipViewTests(TestCase):
    user_factory = UserFactory

    def flag_url(self, name, flag):
        url = self.reverse(name)
        if url.endswith('/'):
            return "{}?{}=1".format(url, flag)
        else:
            return "{}/?{}=1".format(url, flag)

    def test_membership_landing(self):
        flag = 'psf_membership'
        # Ensure 404s without flag
        response = self.get('membership')
        self.response_404(response)

        # Ensure FlagMixin is working
        response = self.client.get(self.flag_url('membership', flag))
        self.response_200(response)
