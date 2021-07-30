from collections import OrderedDict
from django import template

from ..models import Sponsorship, SponsorshipPackage
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
    packages = SponsorshipPackage.objects.all()

    sponsorships_by_package = OrderedDict()
    for pkg in packages:
        key = pkg.name
        sponsorships_by_package[key] = [
            sp
            for sp in sponsorships
            if sp.level_name == key
        ]

    return {
        'logo_place': logo_place,
        'sponsorships': sponsorships,
        'packages': SponsorshipPackage.objects.all(),
        'sponsorships_by_package': sponsorships_by_package,
    }
