from django import template

from ..models import Sponsor


register = template.Library()


@register.inclusion_tag('sponsors/templatetags/featured_sponsor_rotation.html')
def featured_sponsor_rotation():
    """
    Retrieve featured Sponsors for rotation
    """
    return {'sponsors': Sponsor.objects.featured()}
