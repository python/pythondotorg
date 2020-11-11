from django.test import TestCase

from companies.models import Company

from ..models import Sponsor
from ..templatetags.sponsors import featured_sponsor_rotation


class SponsorTemplatetagTests(TestCase):
    def test_templatetag(self):
        sponsors_context = featured_sponsor_rotation()
        self.assertEqual({}, sponsors_context)
