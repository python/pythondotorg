from model_bakery.recipe import Recipe

from sponsors.models import StatementOfWork


empty_sow = Recipe(
    StatementOfWork,
    sponsorship__sponsor__name="Sponsor",
    benefits_list="",
    legal_clauses="",
)

awaiting_signature_sow = Recipe(
    StatementOfWork,
    sponsorship__sponsor__name="Awaiting Sponsor",
    benefits_list="- benefit 1",
    legal_clauses="",
    status=StatementOfWork.AWAITING_SIGNATURE,
)
