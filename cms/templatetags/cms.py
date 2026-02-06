"""Template tags for rendering CMS-related content."""

from django import template
from django.utils.dateformat import format as date_format

register = template.Library()


@register.inclusion_tag("cms/iso_time_tag.html")
def iso_time_tag(date):
    """Render a date as an ISO 8601 time tag with month, day, and year."""
    return {
        "timestamp": date_format(date, "c"),
        "month": date_format(date, "m"),
        "day": date_format(date, "d"),
        "year": date_format(date, "Y"),
    }
