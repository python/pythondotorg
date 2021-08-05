from collections import OrderedDict
from django import template

from ..models import Sponsorship, SponsorshipPackage, Sponsor, TieredQuantityConfiguration
from ..enums import PublisherChoices, LogoPlacementChoices


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

    context = {
        'logo_place': logo_place,
        'sponsorships': sponsorships,
    }

    # organizes logo placement for sponsors page
    # logos must be grouped by package and each package muse use
    # specific dimensions to control the logos' grid
    if logo_place == LogoPlacementChoices.SPONSORS_PAGE.value:
        logo_dimensions = {
            "Visionary": "350",
            "Sustainability": "300",
            "Maintaining": "300",
            "Contributing": "275",
            "Supporting": "250",
            "Partner": "225",
            "Participating": "225",
            "Associate": "175",
        }
        sponsorships_by_package = OrderedDict()
        for pkg in packages:
            key = pkg.name
            sponsorships_by_package[key] = {
                "logo_dimension": logo_dimensions.get(key, "175"),
                "sponsorships": [
                    sp
                    for sp in sponsorships
                    if sp.level_name == key
                ]
            }

        context.update({
            'packages': SponsorshipPackage.objects.all(),
            'sponsorships_by_package': sponsorships_by_package,
        })
    return context


@register.simple_tag
def benefit_quantity_for_package(benefit, package):
    quantity_configuration = TieredQuantityConfiguration.objects.filter(
        benefit=benefit, package=package
    ).first()
    if quantity_configuration is None:
        return ""
    return quantity_configuration.quantity


@register.simple_tag
def benefit_name_for_display(benefit, package):
    return benefit.name_for_display(package=package)
