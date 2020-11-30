from django import template

from ..models import Sponsor


register = template.Library()


@register.inclusion_tag("sponsors/partials/full_sponsorship.txt")
def full_sponsorship(sponsorship):
    return {
        "sponsorship": sponsorship,
        "sponsor": sponsorship.sponsor,
        "benefits": list(sponsorship.benefits.all()),
    }
