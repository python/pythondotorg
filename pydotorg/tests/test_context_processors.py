from model_bakery import baker

from django.urls import reverse
from django.conf import settings
from pydotorg import context_processors
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser


class TemplateProcessorsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_url_name(self):
        request = self.factory.get('/inner/')
        self.assertEqual({'URL_NAMESPACE': '', 'URL_NAME': 'inner'}, context_processors.url_name(request))

        request = self.factory.get('/events/calendars/')
        self.assertEqual({'URL_NAMESPACE': 'events', 'URL_NAME': 'events:calendar_list'}, context_processors.url_name(request))

        request = self.factory.get('/getit-404/releases/3.3.3/not-an-actual-thing/')
        self.assertEqual({'URL_NAMESPACE': None, 'URL_NAME': None}, context_processors.url_name(request))

        request = self.factory.get('/getit-404/releases/3.3.3/\r\n/')
        self.assertEqual({'URL_NAMESPACE': None, 'URL_NAME': None}, context_processors.url_name(request))

        request = self.factory.get('/nothing/here/')
        self.assertEqual({'URL_NAMESPACE': None, 'URL_NAME': None}, context_processors.url_name(request))

    def test_blog_url(self):
        request = self.factory.get('/about/')
        self.assertEqual({'BLOG_URL': settings.PYTHON_BLOG_URL}, context_processors.blog_url(request))

    def test_user_nav_bar_links_for_non_psf_members(self):
        request = self.factory.get('/about/')
        request.user = baker.make(settings.AUTH_USER_MODEL, username='foo')

        expected_nav = {
            "account": {
                "label": "Your Account",
                "urls": [
                    {"url": reverse("users:user_detail", args=['foo']), "label": "View profile"},
                    {"url": reverse("users:user_profile_edit"), "label": "Edit profile"},
                    {"url": reverse("account_change_password"), "label": "Change password"},
                ],
            },
            "psf_membership": {
                "label": "Membership",
                "urls": [
                    {"url": reverse("users:user_nominations_view"), "label": "Nominations"},
                    {"url": reverse("users:user_membership_create"), "label": "Become a PSF Basic member"},
                ],
            },
            "sponsorships": {
                "label": "Sponsorships Dashboard",
                "url": None,
            }
        }

        self.assertEqual(
            {"USER_NAV_BAR": expected_nav},
            context_processors.user_nav_bar_links(request)
        )

    def test_user_nav_bar_links_for_psf_members(self):
        request = self.factory.get('/about/')
        request.user = baker.make(settings.AUTH_USER_MODEL, username='foo')
        baker.make('users.Membership', creator=request.user)

        expected_nav = {
            "account": {
                "label": "Your Account",
                "urls": [
                    {"url": reverse("users:user_detail", args=['foo']), "label": "View profile"},
                    {"url": reverse("users:user_profile_edit"), "label": "Edit profile"},
                    {"url": reverse("account_change_password"), "label": "Change password"},
                ],
            },
            "psf_membership": {
                "label": "Membership",
                "urls": [
                    {"url": reverse("users:user_nominations_view"), "label": "Nominations"},
                    {"url": reverse("users:user_membership_edit"), "label": "Edit PSF Basic membership"},
                ],
            },
            "sponsorships": {
                "label": "Sponsorships Dashboard",
                "url": None,
            }
        }

        self.assertEqual(
            {"USER_NAV_BAR": expected_nav},
            context_processors.user_nav_bar_links(request)
        )

    def test_user_nav_bar_sponsorship_links(self):
        request = self.factory.get('/about/')
        request.user = baker.make(settings.AUTH_USER_MODEL, username='foo')
        baker.make("sponsors.Sponsorship", submited_by=request.user, _quantity=2, _fill_optional=True)

        expected_section = {
            "label": "Sponsorships Dashboard",
            "url": reverse("users:user_sponsorships_dashboard")
        }

        self.assertEqual(
            expected_section,
            context_processors.user_nav_bar_links(request)['USER_NAV_BAR']['sponsorships']
        )

    def test_user_nav_bar_links_for_anonymous_user(self):
        request = self.factory.get('/about/')
        request.user = AnonymousUser()

        self.assertEqual({"USER_NAV_BAR": {}}, context_processors.user_nav_bar_links(request))

    def test_url_name_always_returns_keys(self):
        """Ensure URL_NAME and URL_NAMESPACE are always present in context, even for 404s.
        Because it makes sentry unhappy: https://python-software-foundation.sentry.io/issues/6931306293/
        """
        # test with a 404 path
        request = self.factory.get('/this-does-not-exist/')
        result = context_processors.url_name(request)

        # kyes should always be present
        self.assertIn('URL_NAME', result)
        self.assertIn('URL_NAMESPACE', result)

        # values should be None for unresolved URLs
        self.assertIsNone(result['URL_NAME'])
        self.assertIsNone(result['URL_NAMESPACE'])
