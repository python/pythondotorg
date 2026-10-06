"""Agreement management is granted by named groups, never user permissions."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Concatenate

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from django.contrib.auth.models import AnonymousUser
    from django.http import HttpRequest, HttpResponse

    from apps.users.models import User

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

EDITORS = "Agreements Editors"
ADMINISTRATORS = "Agreements Administrators"


def _in_groups(user: User | AnonymousUser, names: Iterable[str]) -> bool:
    return user.is_authenticated and user.is_active and user.groups.filter(name__in=names).exists()


def can_prepare(user: User | AnonymousUser) -> bool:
    """Allow either group to read records and prepare unoffered drafts."""
    return _in_groups(user, (EDITORS, ADMINISTRATORS))


def is_administrator(user: User | AnonymousUser) -> bool:
    """Reserve configuration and agreement transitions for the administrator group."""
    return _in_groups(user, (ADMINISTRATORS,))


def _role_required[**P](
    check: Callable[[User | AnonymousUser], bool],
) -> Callable[
    [Callable[Concatenate[HttpRequest, P], HttpResponse]], Callable[Concatenate[HttpRequest, P], HttpResponse]
]:
    def decorate(
        view: Callable[Concatenate[HttpRequest, P], HttpResponse],
    ) -> Callable[Concatenate[HttpRequest, P], HttpResponse]:
        @login_required
        @wraps(view)
        def guarded(request: HttpRequest, *args: P.args, **kwargs: P.kwargs) -> HttpResponse:
            if not check(request.user):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return guarded

    return decorate


preparer_required = _role_required(can_prepare)
administrator_required = _role_required(is_administrator)
