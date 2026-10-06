"""Placeholder validation shared by editable agreements, contracts, and terms."""

from django.core.exceptions import ValidationError

from apps.agreements.documents import EFFECTIVE_DATE, SIGNATURES


def _check_placeholders(markdown, *, required):
    """Documents carry the signature placeholder exactly once; staff text written elsewhere, never."""
    count = markdown.count(SIGNATURES)
    if required and count != 1:
        msg = f"Keep {SIGNATURES} exactly once, on its own line: the signature block goes there."
        raise ValidationError(msg)
    if not required and (count or EFFECTIVE_DATE in markdown):
        msg = f"Remove {SIGNATURES} and {EFFECTIVE_DATE}; they are added automatically."
        raise ValidationError(msg)
