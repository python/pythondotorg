"""Template tags for the sponsor management UI."""

from django import template

register = template.Library()

# URL name prefixes mapped to the navbar section they belong to. Checked in
# order, so "manage_sponsorship" must come before "manage_sponsor".
_NAV_SECTIONS = (
    ("manage_dashboard", "dashboard"),
    ("manage_current_year", "dashboard"),
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
    ("manage_assets", "assets"),
    ("manage_clone_year", "clone"),
    ("manage_guide", "guide"),
)

# Sections reached through the navbar's "More" dropdown
MORE_SECTIONS = frozenset({"finances", "sponsors", "legal_clauses", "assets", "clone", "guide"})


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
