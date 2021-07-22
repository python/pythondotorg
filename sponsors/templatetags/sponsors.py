from django import template

from ..models import Sponsorship
from ..enums import PublisherChoices


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


@register.inclusion_tag("sponsors/partials/sponsors-list.html")
def list_sponsors(logo_place, publisher=PublisherChoices.FOUNDATION.value):
    sponsorships = Sponsorship.objects.enabled().with_logo_placement(
        logo_place=logo_place, publisher=publisher
    ).select_related('sponsor')

    return {
        'logo_place': logo_place,
        'sponsorships': sponsorships,
    }
