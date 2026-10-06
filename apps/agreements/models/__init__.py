"""Models registered by the agreements Django app."""

from apps.agreements.models.agreements import (
    MANAGE_PERMISSION,
    Agreement,
    AgreementRevision,
    CustomContract,
    SignedCopy,
    SigningLink,
)
from apps.agreements.models.orders import Order, OrderLine, Program
from apps.agreements.models.terms import CANONICAL_ORIGIN, Terms, TermsVersion

__all__ = [
    "CANONICAL_ORIGIN",
    "MANAGE_PERMISSION",
    "Agreement",
    "AgreementRevision",
    "CustomContract",
    "Order",
    "OrderLine",
    "Program",
    "SignedCopy",
    "SigningLink",
    "Terms",
    "TermsVersion",
]
