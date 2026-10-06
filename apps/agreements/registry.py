"""Kinds of agreement: how a domain app drafts, freezes, and follows up on its documents.

A domain model (a configured order, a custom contract, or a sponsorship) holds the
selections and has a ``OneToOneField`` named ``agreement`` to ``agreements.Agreement``. It
stays editable until it is offered; the workflow then freezes it and sets that field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, cast

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser

    from apps.agreements.models import Agreement, CustomContract, Order, TermsVersion
    from apps.users.models import User


class AgreementDetails(TypedDict):
    """Counterparty identity supplied by a registered draft kind."""

    title: str
    counterparty_name: str
    counterparty_account: User | None


_KINDS: dict[str, Kind[Any]] = {}


class Kind[Subject: (CustomContract, Order)]:
    """Base class for a registered kind of agreement."""

    slug = ""
    name = ""
    model: type[Subject] = cast("type[Subject]", None)

    def details(self, subject: Subject) -> AgreementDetails:
        """Return ``title``, ``counterparty_name``, and ``counterparty_account`` for a new agreement."""
        raise NotImplementedError

    def compose(self, subject: Subject) -> str:
        """Return the document's markdown, with ``documents.SIGNATURES`` where the signatures go."""
        raise NotImplementedError

    def cited_terms_versions(self, subject: Subject) -> list[TermsVersion]:
        """Return the ``TermsVersion`` objects the document cites."""
        return []

    def freeze(self, subject: Subject) -> None:
        """Fix anything the document depends on, such as prices, when it is offered."""

    def release(self, subject: Subject) -> None:
        """Undo ``freeze`` when an offer is withdrawn and the subject becomes editable again."""

    def executed(self, agreement: Agreement) -> None:
        """Act on a fully signed agreement, for example by activating a sponsorship."""

    def can_view(self, user: User | AnonymousUser, agreement: Agreement) -> bool:
        """Whether a user other than PSF staff and the counterparty's account may view it."""
        return False

    def subject(self, agreement: Agreement) -> Subject | None:
        """Return the domain object the agreement was offered for, if it still points at it."""
        return self.model.objects.filter(agreement=agreement).first()


def register[K: Kind[Any]](kind_class: type[K]) -> type[K]:
    """Register a ``Kind`` subclass under its slug."""
    _KINDS[kind_class.slug] = kind_class()
    return kind_class


def get_kind(slug: str) -> Kind[Any]:
    """Return the registered kind for ``slug``."""
    return _KINDS[slug]
