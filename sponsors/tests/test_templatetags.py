from model_bakery import baker
from django.test import TestCase

from companies.models import Company

from ..models import Sponsor
from ..templatetags.sponsors import full_sponsorship


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
