"""Template tags for the sponsor management UI."""

from django import template

register = template.Library()


@register.simple_tag
def days_until(target_date, reference_date):
    """Return the number of days between reference_date and target_date."""
    if not target_date or not reference_date:
        return 0
    return (target_date - reference_date).days
