from model_bakery.recipe import Recipe


empty_sow = Recipe(
    "sponsors.StatementOfWork",
    sponsorship__sponsor__name="Sponsor",
    benefits_list="",
    legal_clauses="",
)

awaiting_signature_sow = Recipe(
    "sponsors.StatementOfWork",
    sponsorship__sponsor__name="Awaiting Sponsor",
    benefits_list="- benefit 1",
    legal_clauses="",
)
