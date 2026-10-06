"""Account lookup shared by contract and order forms."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from apps.users.models import User


def account_for_email(email: str) -> User:
    """Return the one active python.org account using ``email``, or raise ``ValidationError``."""
    accounts = list(get_user_model().objects.filter(email__iexact=email, is_active=True)[:2])
    if len(accounts) != 1:
        msg = (
            "No python.org account uses this email."
            if not accounts
            else "More than one account uses this email; ask which one to use."
        )
        raise ValidationError(msg)
    return cast("User", accounts[0])
