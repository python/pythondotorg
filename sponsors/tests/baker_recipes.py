from datetime import date, timedelta

from model_bakery.recipe import Recipe

from sponsors.models import Contract, LogoPlacement, Sponsorship, SponsorBenefit
from sponsors.enums import LogoPlacementChoices, PublisherChoices

today = date.today()
two_days = timedelta(days=2)

empty_contract = Recipe(
    Contract,
    sponsorship__sponsor__name="Sponsor",
    benefits_list="",
    legal_clauses="",
)

awaiting_signature_contract = Recipe(
    Contract,
    sponsorship__sponsor__name="Awaiting Sponsor",
    benefits_list="- benefit 1",
    legal_clauses="",
    status=Contract.AWAITING_SIGNATURE,
)

finalized_sponsorship = Recipe(
    Sponsorship,
    sponsor__name="Sponsor Name",
    status=Sponsorship.FINALIZED,
    start_date=today - two_days,
    end_date=today + two_days,
)

logo_at_download_feature = Recipe(
    LogoPlacement,
    publisher=PublisherChoices.FOUNDATION.value,
    logo_place=LogoPlacementChoices.DOWNLOAD_PAGE.value,
)

logo_at_sponsors_feature = Recipe(
    LogoPlacement,
    publisher=PublisherChoices.FOUNDATION.value,
    logo_place=LogoPlacementChoices.SPONSORS_PAGE.value,
)
