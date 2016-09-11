from django.test import TestCase

from waffle.testutils import override_flag


class MembershipViewTests(TestCase):

    @override_flag('psf_membership', active=False)
    def test_membership_landing_ensure_404(self):
        response = self.client.get('/membership/')
        self.assertEqual(response.status_code, 404)

    @override_flag('psf_membership', active=True)
    def test_membership_landing(self):
        # Ensure FlagMixin is working
        response = self.client.get('/membership/')
        self.assertEqual(response.status_code, 200)
