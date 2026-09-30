from django.test import TestCase
from django.urls import reverse
from model_bakery import baker

from apps.sponsors.models import SponsorBenefit, Sponsorship
from apps.sponsors.models.benefits import ProvidedTextAsset


class AssetMixinTests(TestCase):
    def setUp(self):
        self.sponsorship = baker.make(Sponsorship)
        self.sponsor_benefit = baker.make(SponsorBenefit, sponsorship=self.sponsorship)
        # ProvidedTextAsset inherits from ProvidedAssetMixin which inherits from AssetMixin
        self.asset = baker.make(ProvidedTextAsset, sponsor_benefit=self.sponsor_benefit, internal_name="test_asset")

    def test_user_view_url_includes_anchor(self):
        expected_url = reverse("users:sponsorship_application_detail", args=[self.sponsorship.pk])
        expected_url += "#provided-assets-info"

        self.assertEqual(self.asset.user_view_url, expected_url)
        self.assertIn("#provided-assets-info", self.asset.user_view_url)
