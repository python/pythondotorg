from model_bakery import baker
from django.test import TestCase

from companies.models import Company

from ..models import Sponsor, SponsorBenefit
from ..templatetags.sponsors import full_sponsorship, list_sponsors


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


class ListSponsorsTemplateTag(TestCase):

    def test_filter_sponsorship_with_logo_placement_benefits(self):
        sponsorship = baker.make_recipe('sponsors.tests.finalized_sponsorship')
        baker.make_recipe(
            'sponsors.tests.logo_at_download_feature',
            sponsor_benefit__sponsorship=sponsorship
        )

        context = list_sponsors("download")

        self.assertEqual("download", context["logo_place"])
        self.assertEqual(1, len(context["sponsorships"]))
        self.assertIn(sponsorship, context["sponsorships"])
