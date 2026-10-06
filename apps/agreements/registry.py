"""Kinds of agreement: how a domain app drafts, freezes, and follows up on its documents.

A domain model (a configured order, a custom contract, or a sponsorship) holds the
selections and has a ``OneToOneField`` named ``agreement`` to ``agreements.Agreement``. It
stays editable until it is offered; the workflow then freezes it and sets that field.
"""

_KINDS = {}


class Kind:
    """Base class for a registered kind of agreement."""

    slug = ""
    name = ""
    model = None

    def details(self, subject):
        """Return ``title``, ``counterparty_name``, and ``counterparty_account`` for a new agreement."""
        raise NotImplementedError

    def compose(self, subject):
        """Return the document's markdown, with ``documents.SIGNATURES`` where the signatures go."""
        raise NotImplementedError

    def cited_terms_versions(self, subject):
        """Return the ``TermsVersion`` objects the document cites."""
        return []

    def freeze(self, subject):
        """Fix anything the document depends on, such as prices, when it is offered."""

    def release(self, subject):
        """Undo ``freeze`` when an offer is withdrawn and the subject becomes editable again."""

    def executed(self, agreement):
        """Act on a fully signed agreement, for example by activating a sponsorship."""

    def can_view(self, user, agreement):
        """Whether a user other than PSF staff and the counterparty's account may view it."""
        return False

    def subject(self, agreement):
        """Return the domain object the agreement was offered for, if it still points at it."""
        return self.model.objects.filter(agreement=agreement).first()


def register(kind_class):
    """Register a ``Kind`` subclass under its slug."""
    _KINDS[kind_class.slug] = kind_class()
    return kind_class


def get_kind(slug):
    """Return the registered kind for ``slug``."""
    return _KINDS[slug]
