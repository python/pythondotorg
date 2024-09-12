import math

from collections import OrderedDict
from django import template
from django.conf import settings
from django.core.cache import cache

from ..models import Sponsorship, SponsorshipPackage, TieredBenefitConfiguration
from sponsors.models.enums import PublisherChoices, LogoPlacementChoices


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
    ).order_by('package').select_related('sponsor', 'package')
    packages = SponsorshipPackage.objects.all()

    context = {
        'logo_place': logo_place,
        'sponsorships': sponsorships,
    }

    # organizes logo placement for sponsors page
    # logos must be grouped by package and each package muse use
    # specific dimensions to control the logos' grid
    if logo_place == LogoPlacementChoices.SPONSORS_PAGE.value:
        sponsorships_by_package = OrderedDict()
        for pkg in packages:
            sponsorships_by_package[pkg.slug] = {
                "label": pkg.name,
                "logo_dimension": str(pkg.logo_dimension),
                "sponsorships": [
                    sp
                    for sp in sponsorships
                    if sp.package.slug == pkg.slug
                ]
            }

        context.update({
            'packages': SponsorshipPackage.objects.all(),
            'sponsorships_by_package': sponsorships_by_package,
        })

    return context


@register.simple_tag
def benefit_quantity_for_package(benefit, package):
    quantity_configuration = TieredBenefitConfiguration.objects.filter(
        benefit=benefit, package=package
    ).first()
    if quantity_configuration is None:
        return ""
    return quantity_configuration.display_label or quantity_configuration.quantity


@register.simple_tag
def benefit_name_for_display(benefit, package):
    return benefit.name_for_display(package=package)


@register.filter
def ideal_size(image, ideal_dimension):
    ideal_dimension = int(ideal_dimension)
    try:
        w, h = image.width, image.height
    except FileNotFoundError:
        # local dev doesn't have all images if DB is a copy from prod environment
        # this is just a fallback to return ideal_dimension instead
        w, h = ideal_dimension, ideal_dimension

    return int(
        w * math.sqrt((100 * ideal_dimension) / (w * h))
    )
