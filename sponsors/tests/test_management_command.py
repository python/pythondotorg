from django.test import TestCase

from model_bakery import baker

from unittest import mock

from sponsors.models import ProvidedTextAssetConfiguration, ProvidedTextAsset
from sponsors.models.enums import AssetsRelatedTo

from sponsors.management.commands.create_pycon_vouchers_for_sponsors import (
    generate_voucher_codes,
    BENEFITS,
)


class CreatePyConVouchersForSponsorsTestCase(TestCase):
    @mock.patch(
        "sponsors.management.commands.create_pycon_vouchers_for_sponsors.api_call",
        return_value={"code": 200, "data": {"promo_code": "test-promo-code"}},
    )
    def test_generate_voucher_codes(self, mock_api_call):
        for benefit_id, code in BENEFITS.items():
            sponsor = baker.make("sponsors.Sponsor", name="Foo")
            sponsorship = baker.make(
                "sponsors.Sponsorship", status="finalized", sponsor=sponsor
            )
            sponsorship_benefit = baker.make(
                "sponsors.SponsorshipBenefit", id=benefit_id
            )
            sponsor_benefit = baker.make(
                "sponsors.SponsorBenefit",
                id=benefit_id,
                sponsorship=sponsorship,
                sponsorship_benefit=sponsorship_benefit,
            )
            quantity = baker.make(
                "sponsors.TieredBenefit",
                sponsor_benefit=sponsor_benefit,
            )
            config = baker.make(
                ProvidedTextAssetConfiguration,
                related_to=AssetsRelatedTo.SPONSORSHIP.value,
                _fill_optional=True,
                internal_name=code["internal_name"],
            )
            asset = config.create_benefit_feature(sponsor_benefit=sponsor_benefit)

        generate_voucher_codes(2020)

        for benefit_id, code in BENEFITS.items():
            asset = ProvidedTextAsset.objects.get(
                sponsor_benefit__id=benefit_id, internal_name=code["internal_name"]
            )
            self.assertEqual(asset.value, "test-promo-code")
