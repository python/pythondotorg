"""Shared helpers for the nominations test suite."""

import datetime

from django.utils import timezone

from apps.nominations.models import Election, ElectionKind


def packaging_council_kind():
    """Return an ElectionKind that uses the Packaging Council nomination form."""
    return ElectionKind.objects.create(
        name="Packaging Council",
        nomination_form=ElectionKind.NominationFormVariant.PACKAGING_COUNCIL,
    )


def open_election(name, kind=None, **extra):
    """Create an election whose nomination window is currently open."""
    now = timezone.now()
    return Election.objects.create(
        name=name,
        date=(now + datetime.timedelta(days=30)).date(),
        kind=kind,
        nominations_open_at=now - datetime.timedelta(days=1),
        nominations_close_at=now + datetime.timedelta(days=1),
        **extra,
    )


def nomination_payload(**overrides):
    """Return a minimally valid nomination POST payload."""
    data = {
        "name": "Grace Hopper",
        "email": "grace@example.com",
        "previous_service": "no",
        "employer": "US Navy",
        "other_affiliations": "",
        "nomination_statement": "A strong candidate.",
    }
    data.update(overrides)
    return data
