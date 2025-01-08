import os
from hashlib import sha1
from calendar import timegm
from datetime import datetime
import sys
from urllib.parse import urlencode

import requests
from requests.exceptions import RequestException

from django.db.models import Q
from django.conf import settings
from django.core.management import BaseCommand

from sponsors.models import (
    SponsorBenefit,
    BenefitFeature,
    ProvidedTextAsset,
    TieredBenefit,
)

BENEFITS = {
    241: {
        "internal_name": "full_conference_passes_code_2025",
        "voucher_type": "SPNS_COMP_",
    },
    259: {
        "internal_name": "pycon_expo_hall_only_passes_code_2025",
        "voucher_type": "SPNS_EXPO_COMP_",
    },
    265: {
        "internal_name": "pycon_additional_full_conference_passes_code_2025",
        "voucher_type": "SPNS_ADDL_DISC_REG_",
    },
    #225: {
    #    "internal_name": "online_only_conference_passes_2025",
    #    "voucher_type": "SPNS_ONLINE_COMP_",
    #},
    292: {
        "internal_name": "pycon_additional_expo_hall_only_passes_2025",
        "voucher_type": "SPNS_EXPO_DISC_",
    },
}


def api_call(uri, query):
    method = "GET"
    body = ""

    timestamp = timegm(datetime.utcnow().timetuple())
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
        "X-API-Signature": str(sha1(base_string.encode("utf-8")).hexdigest()),
        "X-API-Timestamp": str(timestamp),
    }
    scheme = "http" if settings.DEBUG else "https"
    url = f"{scheme}://{settings.PYCON_API_HOST}{uri}"
    try:
        return requests.get(url, headers=headers, params=query).json()
    except RequestException:
        raise


def generate_voucher_codes(year):
    for benefit_id, code in BENEFITS.items():
        for sponsorbenefit in (
            SponsorBenefit.objects.filter(sponsorship_benefit_id=benefit_id)
            .filter(sponsorship__status="finalized")
            .all()
        ):
            try:
                quantity = BenefitFeature.objects.instance_of(TieredBenefit).get(
                    sponsor_benefit=sponsorbenefit
                )
            except BenefitFeature.DoesNotExist:
                print(
                    f"No quantity found for {sponsorbenefit.sponsorship.sponsor.name} and {code['internal_name']}"
                )
                continue
            try:
                asset = ProvidedTextAsset.objects.filter(
                    sponsor_benefit=sponsorbenefit
                ).get(internal_name=code["internal_name"])
            except ProvidedTextAsset.DoesNotExist:
                print(
                    f"No provided asset found for {sponsorbenefit.sponsorship.sponsor.name} with internal name {code['internal_name']}"
                )
                continue

            result = api_call(
                f"/{year}/api/vouchers/",
                query={
                    "voucher_type": code["voucher_type"],
                    "quantity": quantity.quantity,
                    "sponsor_name": sponsorbenefit.sponsorship.sponsor.name,
                },
            )
            if result["code"] == 200:
                print(
                    f"Fullfilling {code['internal_name']} for {sponsorbenefit.sponsorship.sponsor.name}: {quantity.quantity}"
                )
                promo_code = result["data"]["promo_code"]
                asset.value = promo_code
                asset.save()
            else:
                print(
                    f"Error from PyCon when fullfilling {code['internal_name']} for {sponsorbenefit.sponsorship.sponsor.name}: {result}"
                )
    print(f"Done!")


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
