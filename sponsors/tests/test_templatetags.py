from model_bakery import baker
from django.test import TestCase

from companies.models import Company

from ..models import Sponsor
from ..templatetags.sponsors import featured_sponsor_rotation, full_sponsorship


class SponsorTemplatetagTests(TestCase):
    def test_templatetag(self):
        sponsors_context = featured_sponsor_rotation()
        self.assertEqual({}, sponsors_context)


class FullSponsorshipTemplatetagTests(TestCase):
    def test_templatetag_context(self):
        sponsorship = baker.make("sponsors.Sponsorship", _fill_optional=True)
        context = full_sponsorship(sponsorship)
        expected = {
            "sponsorship": sponsorship,
            "sponsor": sponsorship.sponsor,
            "benefits": list(sponsorship.benefits.all()),
        }
        self.assertEqual(context, expected)
