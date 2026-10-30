"""Template tags for the sponsor management UI."""

import datetime

from django import template
from django.utils import timezone

from apps.sponsors.models import SponsorshipCurrentYear

register = template.Library()

# The active sponsorship year rolls over after PyCon US; June 1 is the agreed switch date.
ACTIVE_YEAR_ROLLOVER = (6, 1)


def expected_active_year(today):
    """Return the sponsorship year that should be active on ``today``: next year from June 1 on."""
    rollover = datetime.date(today.year, *ACTIVE_YEAR_ROLLOVER)
    return today.year + 1 if today >= rollover else today.year


@register.simple_tag
def active_year_nudge():
    """Return the year staff should switch to when the active year is behind, else None."""
    expected = expected_active_year(timezone.localdate())
    try:
        current = SponsorshipCurrentYear.get_year()
    except SponsorshipCurrentYear.DoesNotExist:
        return expected
    return expected if current < expected else None


# URL name prefixes mapped to the navbar section they belong to. Checked in
# order, so "manage_sponsorship" must come before "manage_sponsor".
_NAV_SECTIONS = (
    ("manage_dashboard", "dashboard"),
    ("manage_current_year", "current_year"),
    ("manage_sponsorship", "sponsorships"),
    ("manage_bulk_", "sponsorships"),
    ("manage_contract_", "sponsorships"),
    ("manage_contact_", "sponsorships"),
    ("manage_composer", "composer"),
    ("manage_benefit", "benefits"),
    ("manage_package", "packages"),
    ("manage_notification", "notifications"),
    ("manage_finances", "finances"),
    ("manage_sponsor", "sponsors"),
    ("manage_legal_clause", "legal_clauses"),
    ("manage_program", "programs"),
    ("manage_assets", "assets"),
    ("manage_clone_year", "clone"),
    ("manage_guide", "guide"),
)

# Sections reached through the navbar's "More" dropdown
MORE_SECTIONS = frozenset(
    {"finances", "sponsors", "programs", "legal_clauses", "assets", "clone", "current_year", "guide"}
)


@register.simple_tag
def days_until(target_date, reference_date):
    """Return the number of days between reference_date and target_date."""
    if not target_date or not reference_date:
        return 0
    return (target_date - reference_date).days


@register.simple_tag(takes_context=True)
def manage_nav_section(context):
    """Return the navbar section for the current manage page, or "" if none matches."""
    request = context.get("request")
    match = getattr(request, "resolver_match", None)
    url_name = getattr(match, "url_name", None) or ""
    for prefix, section in _NAV_SECTIONS:
        if url_name.startswith(prefix):
            return section
    return ""


@register.filter
def is_more_section(section):
    """Return whether the section lives under the navbar's "More" dropdown."""
    return section in MORE_SECTIONS
