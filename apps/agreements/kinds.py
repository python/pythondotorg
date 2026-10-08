"""The built-in kind for one-off contracts written by PSF staff."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from apps.agreements.models import TermsVersion
    from apps.agreements.registry import AgreementDetails

from apps.agreements.documents import PROVIDER_PREAMBLE, SIGNATURES, md
from apps.agreements.models import CustomContract
from apps.agreements.registry import Kind, register


@register
class CustomContractKind(Kind[CustomContract]):
    """A contract written in full by PSF staff, optionally citing published terms."""

    slug = "custom"
    name = "Custom contract"
    model = CustomContract

    def details(self, subject: CustomContract) -> AgreementDetails:
        """Title and counterparty come straight from the draft."""
        return {
            "title": subject.title,
            "counterparty_name": subject.counterparty_name,
            "counterparty_account": subject.counterparty_account,
        }

    def cited_terms_versions(self, subject: CustomContract) -> list[TermsVersion]:
        """Cite the current version of the chosen terms, if any."""
        return [cast("TermsVersion", subject.terms.current_version)] if subject.terms else []

    def compose(self, subject: CustomContract) -> str:
        """Parties, an optional citation of the terms, the staff-written text, and signatures."""
        parties = (
            f"This agreement is entered into between {PROVIDER_PREAMBLE}, and **{md(subject.counterparty_name)}** "
            '(the "Counterparty").'
        )
        parts = [f"# {md(subject.title)}", "", parties, ""]
        if subject.terms:
            version = cast("TermsVersion", subject.terms.current_version)
            parts += [
                (
                    f"It incorporates by reference the **{md(subject.terms.title)}**, version {md(version.version)}, "
                    f"published at <{version.permanent_url}>. If this agreement "
                    "conflicts with those terms, this agreement controls."
                ),
                "",
            ]
        return "\n".join(
            [
                *parts,
                subject.body_markdown.strip(),
                "",
                "## Signatures",
                "",
                "Each party signs as of the date of the last signature below.",
                "",
                SIGNATURES,
                "",
            ]
        )
