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

API_KEY = settings.PYCON_API_KEY
API_SECRET = settings.PYCON_API_SECRET
API_HOST = settings.PYCON_API_HOST

BENEFITS = {
    64: "full_conference_passes",
    65: "expo_hall_only_passes",
    77: "additional_full_conference_passes",
    73: "additional_expo_hall_only_passes",
}


def api_call(uri, query):
    method = "GET"
    body = ""

    timestamp = timegm(datetime.utcnow().timetuple())
    base_string = "".join(
        (
            API_SECRET,
            str(timestamp),
            method.upper(),
            f"{uri}?{urlencode(query)}",
            body,
        )
    )

    headers = {
        "X-API-Key": str(API_KEY),
        "X-API-Signature": str(sha1(base_string.encode("utf-8")).hexdigest()),
        "X-API-Timestamp": str(timestamp),
    }
    scheme = "http" if settings.DEBUG else "https"
    url = f"{scheme}://{API_HOST}{uri}"
    try:
        return requests.get(url, headers=headers, params=query).json()
    except RequestException:
        raise


class Command(BaseCommand):
    """
    Create Contract objects for existing approved Sponsorships.

    Run this command as a initial data migration or to make sure
    all approved Sponsorships do have associated Contract objects.
    """

    help = "Create Contract objects for existing approved Sponsorships."

    def handle(self, **options):
        for benefit, code_type in BENEFITS.items():
            for sponsorbenefit in (
                SponsorBenefit.objects.filter(sponsorship_benefit_id=benefit)
                .filter(sponsorship__status="finalized")
                .all()
            ):
                try:
                    quantity = BenefitFeature.objects.instance_of(TieredBenefit).get(
                        sponsor_benefit=sponsorbenefit
                    )
                except BenefitFeature.DoesNotExist:
                    print(
                        f"No quantity found for {sponsorbenefit.sponsorship.sponsor.name} and {code_type}"
                    )
                    continue
                try:
                    asset = ProvidedTextAsset.objects.filter(
                        sponsor_benefit=sponsorbenefit
                    ).get(internal_name=f"{code_type}_code")
                except ProvidedTextAsset.DoesNotExist:
                    print(
                        f"No provided asset found for {sponsorbenefit.sponsorship.sponsor.name} with internal name {code_type}_code"
                    )
                    continue

                result = api_call(
                    "/2022/api/promo_codes/generate/",
                    query={
                        "type": code_type,
                        "quantity": quantity.quantity,
                        "sponsor_name": sponsorbenefit.sponsorship.sponsor.name,
                    },
                )
                if result["code"] == 200:
                    print(
                        f"Fullfilling {code_type} for {sponsorbenefit.sponsorship.sponsor.name}: {quantity.quantity}"
                    )
                    promo_code = result["data"]["promo_code"]
                    asset.value = promo_code
                    asset.save()
                else:
                    print(
                        f"Error from PyCon when fullfilling {code_type} for {sponsorbenefit.sponsorship.sponsor.name}: {result}"
                    )
        print(f"Done!")
