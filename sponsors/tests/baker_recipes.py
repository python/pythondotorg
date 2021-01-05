from model_bakery.recipe import Recipe

from sponsors.models import Contract


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
