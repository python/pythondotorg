from model_bakery.recipe import Recipe

from sponsors.models import Contract, LogoPlacement, Sponsorship, SponsorBenefit
from sponsors.enums import LogoPlacementChoices, PublisherChoices


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
