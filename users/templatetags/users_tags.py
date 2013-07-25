from django import template

register = template.Library()


@register.simple_tag(name='location')
def parse_location(user):
    """
    Returns a formatted string of user location data.
    Adds a comma if the city is present, adds a space is the region is present

    Returns empty if no location data is present
    """
    path = ''
    if user.city:
        path += "%s, " % (user.city)
    if user.region:
        path += "%s " % (user.region)
    if user.country:
        path += "%s" % (user.country)
    if len(path) == 0:
        path = "Not Specified"

    return path
