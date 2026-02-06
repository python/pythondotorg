from calendar import timegm
from datetime import UTC, datetime
from hashlib import sha1
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.management import BaseCommand

from sponsors.models import (
    BenefitFeature,
    ProvidedTextAsset,
    SponsorBenefit,
    TieredBenefit,
)

BENEFITS = {
    331: {
        "internal_name": "full_conference_passes_code_2026",
        "voucher_type": "SPNS_COMP_",
    },
    348: {
        "internal_name": "pycon_expo_hall_only_passes_code_2026",
        "voucher_type": "SPNS_EXPO_COMP_",
    },
    353: {
        "internal_name": "pycon_additional_full_conference_passes_code_2026",
        "voucher_type": "SPNS_ADDL_DISC_REG_",
    },
    375: {
        "internal_name": "pycon_additional_expo_hall_only_passes_2026",
        "voucher_type": "SPNS_EXPO_DISC_",
    },
}


def api_call(uri, query):
    method = "GET"
    body = ""

    timestamp = timegm(datetime.now(tz=UTC).timetuple())
    base_string = "".join(
        (
            settings.PYCON_API_SECRET,
            str(timestamp),
            method.upper(),
            f"{uri}?{urlencode(query)}",
            body,
        )
    )

    headers = {
        "X-API-Key": str(settings.PYCON_API_KEY),
        "X-API-Signature": str(sha1(base_string.encode("utf-8")).hexdigest()),  # noqa: S324 - API signature, not for security storage
        "X-API-Timestamp": str(timestamp),
    }
    scheme = "http" if settings.DEBUG else "https"
    url = f"{scheme}://{settings.PYCON_API_HOST}{uri}"
    r = requests.get(url, headers=headers, params=query, timeout=30)
    return r.json()


HTTP_OK = 200


def generate_voucher_codes(year):
    for benefit_id, code in BENEFITS.items():
        for sponsorbenefit in (
            SponsorBenefit.objects.filter(sponsorship_benefit_id=benefit_id)
            .filter(sponsorship__status="finalized")
            .all()
        ):
            try:
                quantity = BenefitFeature.objects.instance_of(TieredBenefit).get(sponsor_benefit=sponsorbenefit)
            except BenefitFeature.DoesNotExist:
                continue
            try:
                asset = ProvidedTextAsset.objects.filter(sponsor_benefit=sponsorbenefit).get(
                    internal_name=code["internal_name"]
                )
            except ProvidedTextAsset.DoesNotExist:
                continue

            result = api_call(
                f"/{year}/api/vouchers/",
                query={
                    "voucher_type": code["voucher_type"],
                    "quantity": quantity.quantity,
                    "sponsor_name": sponsorbenefit.sponsorship.sponsor.name,
                    "sponsor_id": sponsorbenefit.sponsorship.sponsor.id,
                },
            )
            if result["code"] == HTTP_OK:
                promo_code = result["data"]["promo_code"]
                asset.value = promo_code
                asset.save()
            else:
                pass


class Command(BaseCommand):
    """
    Create Contract objects for existing approved Sponsorships.

    Run this command as a initial data migration or to make sure
    all approved Sponsorships do have associated Contract objects.
    """

    help = "Create Contract objects for existing approved Sponsorships."

    def add_arguments(self, parser):
        parser.add_argument("year")

    def handle(self, **options):
        year = options["year"]
        generate_voucher_codes(year)
