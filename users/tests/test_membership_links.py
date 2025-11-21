from django.test import TestCase, RequestFactory
from django.template import Context, Template
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from users.models import Membership

User = get_user_model()

class MembershipLinkTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='123')
        self.template = Template("""
            {% include 'includes/authenticated.html' %}
        """)

    def render_template(self, user):
        request = self.factory.get('/')
        request.user = user
        return self.template.render(Context({'user': user, 'request': request}))

    def test_anonymous_user(self):
        html = self.render_template(AnonymousUser())
        # Anonymous users should see "Sign In"
        self.assertIn('Sign In', html)

    def test_logged_in_non_member(self):
        html = self.render_template(self.user)
        # Logged-in but not a member -> should see the membership join link
        self.assertIn('Become a PSF Basic member', html)

    def test_logged_in_member(self):
        Membership.objects.create(creator=self.user)
        html = self.render_template(self.user)
        self.assertIn('Edit your PSF Basic membership', html)
