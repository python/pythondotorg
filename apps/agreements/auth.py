"""Agreement management is granted by named groups, never user permissions."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

EDITORS = "Agreements Editors"
ADMINISTRATORS = "Agreements Administrators"


def _in_groups(user, names):
    return user.is_authenticated and user.is_active and user.groups.filter(name__in=names).exists()


def can_prepare(user):
    """Allow either group to read records and prepare unoffered drafts."""
    return _in_groups(user, (EDITORS, ADMINISTRATORS))


def is_administrator(user):
    """Reserve configuration and agreement transitions for the administrator group."""
    return _in_groups(user, (ADMINISTRATORS,))


def _role_required(check):
    def decorate(view):
        @login_required
        @wraps(view)
        def guarded(request, *args, **kwargs):
            if not check(request.user):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return guarded

    return decorate


preparer_required = _role_required(can_prepare)
administrator_required = _role_required(is_administrator)
