from django import template

from ..models import Sponsor


register = template.Library()


@register.inclusion_tag("sponsors/partials/full_sponsorship.txt")
def full_sponsorship(sponsorship, display_fee=False):
    if not display_fee:
        display_fee = not sponsorship.for_modified_package
    return {
        "sponsorship": sponsorship,
        "sponsor": sponsorship.sponsor,
        "benefits": list(sponsorship.benefits.all()),
        "display_fee": display_fee,
    }
