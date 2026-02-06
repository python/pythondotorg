"""Template tags for displaying upcoming events."""

from django import template
from django.utils import timezone

from apps.events.models import Event

register = template.Library()


@register.simple_tag
def get_events_upcoming(limit=5, only_featured=False):
    """Return upcoming events, optionally filtered to featured only."""
    qs = Event.objects.for_datetime(timezone.now()).order_by("occurring_rule__dt_start")
    if only_featured:
        qs = qs.filter(featured=True)
    return qs[:limit]
