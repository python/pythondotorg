from model_bakery import baker
from django.test import TestCase

from companies.models import Company

from ..models import Sponsor
from ..templatetags.sponsors import full_sponsorship


class FullSponsorshipTemplatetagTests(TestCase):
    def test_templatetag_context(self):
        sponsorship = baker.make(
            "sponsors.Sponsorship", for_modified_package=False, _fill_optional=True
        )
        context = full_sponsorship(sponsorship)
        expected = {
            "sponsorship": sponsorship,
            "sponsor": sponsorship.sponsor,
            "benefits": list(sponsorship.benefits.all()),
            "display_fee": True,
        }
        self.assertEqual(context, expected)

    def test_do_not_display_fee_if_modified_package(self):
        sponsorship = baker.make(
            "sponsors.Sponsorship", for_modified_package=True, _fill_optional=True
        )
        context = full_sponsorship(sponsorship)
        self.assertFalse(context["display_fee"])

    def test_allows_to_overwrite_display_fee_flag(self):
        sponsorship = baker.make(
            "sponsors.Sponsorship", for_modified_package=True, _fill_optional=True
        )
        context = full_sponsorship(sponsorship, display_fee=True)
        self.assertTrue(context["display_fee"])
