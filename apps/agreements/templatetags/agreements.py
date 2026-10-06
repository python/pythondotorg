"""Template helpers for agreement pages."""

from django import template

from apps.agreements.auth import can_prepare, is_administrator
from apps.agreements.orders.pricing import money

register = template.Library()
register.filter("money", money)
register.filter("can_prepare_agreements", can_prepare)
register.filter("is_agreements_administrator", is_administrator)

STATUSES = {
    "draft": ("neutral", "Draft"),
    "offered": ("notice", "Awaiting signature"),
    "signed": ("notice", "Awaiting countersignature"),
    "executed": ("success", "Active"),
    "declined": ("error", "Declined"),
    "withdrawn": ("neutral", "Withdrawn"),
}


@register.inclusion_tag("agreements/_status.html")
def status_badge(status):
    """Status pill for an agreement or a draft; an executed agreement reads as Active."""
    tone, label = STATUSES[status]
    return {"tone": tone, "label": label}
