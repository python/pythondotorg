from django import template

from ..models import Sponsor


register = template.Library()


@register.inclusion_tag("sponsors/templatetags/featured_sponsor_rotation.html")
def featured_sponsor_rotation():
    """
    Retrieve featured Sponsors for rotation
    """
    # TODO remove this code completely if not necessary
    # this templatetag logic was removed by the PR #1667
    # the Sponsor model got updated and its previous use was deprecated
    # this templated tag is used at https://www.python.org/psf-landing/ but since the prod
    # DB doesn't have any published sponsor, the default message is being print
    return {}


@register.inclusion_tag("sponsors/partials/full_sponsorship.txt")
def full_sponsorship(sponsorship):
    return {
        "sponsorship": sponsorship,
        "sponsor": sponsorship.sponsor,
        "benefits": list(sponsorship.benefits.all()),
    }
