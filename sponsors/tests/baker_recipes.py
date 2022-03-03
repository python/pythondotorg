from datetime import date, timedelta

from model_bakery.recipe import Recipe, foreign_key

from sponsors.models import Contract, LogoPlacement, Sponsorship, SponsorshipPackage
from sponsors.models.enums import LogoPlacementChoices, PublisherChoices

today = date.today()
two_days = timedelta(days=2)
thirty_days = timedelta(days=30)

empty_contract = Recipe(
    Contract,
    sponsorship__sponsor__name="Sponsor",
    sponsorship__start_date=today,
    sponsorship__end_date=today + thirty_days,
    benefits_list="",
    legal_clauses="",
)

awaiting_signature_contract = Recipe(
    Contract,
    sponsorship__sponsor__name="Awaiting Sponsor",
    sponsorship__start_date=today,
    sponsorship__end_date=today + thirty_days,
    benefits_list="- benefit 1",
    legal_clauses="",
    status=Contract.AWAITING_SIGNATURE,
)

package = Recipe(
    SponsorshipPackage
)

finalized_sponsorship = Recipe(
    Sponsorship,
    sponsor__name="Sponsor Name",
    status=Sponsorship.FINALIZED,
    start_date=today - two_days,
    end_date=today + two_days,
    package=foreign_key(package),
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

logo_at_pypi_feature = Recipe(
    LogoPlacement,
    publisher=PublisherChoices.PYPI.value,
    logo_place=LogoPlacementChoices.SIDEBAR.value,
)
