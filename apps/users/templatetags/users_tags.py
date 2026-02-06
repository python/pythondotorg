"""Template tags and filters for user profile display."""

from django import template

from apps.users.models import Membership

register = template.Library()


@register.filter(name="user_location")
def parse_location(user):
    """Return a formatted string of user location data.

    Add a comma if the city is present, add a space if the region is present.
    Return empty if no location data is present.
    """
    path = ""

    try:
        membership = user.membership
    except Membership.DoesNotExist:
        return ""

    if membership.city:
        path += f"{membership.city}"
    if membership.region:
        if membership.city:
            path += ", "
        path += f"{membership.region}"
    if membership.country:
        if membership.region:
            path += " "
        elif membership.city:
            path += ", "
        path += f"{membership.country}"

    return path
