"""Template tags and filters for rendering sponsor information."""

import math
from collections import OrderedDict

from django import template
from django.utils.safestring import mark_safe
from sorl.thumbnail import default as thumbnail_default
from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.images import ImageFile

from apps.sponsors.models import Sponsorship, SponsorshipPackage, TieredBenefitConfiguration
from apps.sponsors.models.enums import LogoPlacementChoices, PublisherChoices

register = template.Library()


# Backslash-escape every ASCII punctuation char (Pandoc renders each as a literal) so
# user input can't form a Markdown or raw-TeX construct in any context.
MARKDOWN_SPECIAL_CHARS = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


@register.filter
def escape_markdown(value):
    """Escape a sponsor-supplied value so Pandoc renders it as literal text."""
    # mark_safe: the output goes to Pandoc (PDF/DOCX), not HTML, so it is not an XSS
    # sink; it only stops Django autoescaping from interfering with the escaping here.
    return mark_safe("".join("\\" + ch if ch in MARKDOWN_SPECIAL_CHARS else ch for ch in str(value)))  # noqa: S308


@register.inclusion_tag("sponsors/partials/full_sponsorship.txt")
def full_sponsorship(sponsorship, display_fee=False):
    """Render a full sponsorship detail block with benefits and fee information."""
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
    """Render a list of sponsors filtered by logo placement and publisher."""
    sponsorships = (
        Sponsorship.objects.enabled()
        .with_logo_placement(logo_place=logo_place, publisher=publisher)
        .order_by("package")
        .select_related("sponsor", "package")
    )
    packages = SponsorshipPackage.objects.all()

    context = {
        "logo_place": logo_place,
        "sponsorships": sponsorships,
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
                "sponsorships": [sp for sp in sponsorships if sp.package.slug == pkg.slug],
            }

        context.update(
            {
                "packages": SponsorshipPackage.objects.all(),
                "sponsorships_by_package": sponsorships_by_package,
            }
        )

    return context


@register.simple_tag
def benefit_quantity_for_package(benefit, package):
    """Return the configured quantity label for a benefit within a package."""
    quantity_configuration = TieredBenefitConfiguration.objects.filter(benefit=benefit, package=package).first()
    if quantity_configuration is None:
        return ""
    return quantity_configuration.display_label or quantity_configuration.quantity


@register.simple_tag
def benefit_name_for_display(benefit, package):
    """Return the display name for a benefit, customized per package if applicable."""
    return benefit.name_for_display(package=package)


@register.simple_tag
def sponsor_logo(image, ideal_dimension):
    """Size a logo so every sponsor in a tier gets the same visual area, with 1x and 2x PNG renditions.

    The source size comes from sorl's key-value store: reading ``image.width`` would download
    the full original from S3 on every render, while sorl records the size once per image.
    Returns ``None`` when no file is associated with the field.
    """
    if not image:
        return None
    ideal_dimension = int(ideal_dimension)
    try:
        source_width, source_height = thumbnail_default.kvstore.get_or_set(ImageFile(image)).size
    except FileNotFoundError:
        # local dev doesn't have all images if DB is a copy from prod environment;
        # size it as a square logo would be instead of erroring.
        width = int(math.sqrt(100 * ideal_dimension))
        return {"src": image.url, "srcset": f"{image.url} {width}w", "width": width, "height": width}

    # Equal area per logo, but no wider than the tier's grid column (ideal_dimension px).
    width = min(int(math.sqrt(100 * ideal_dimension * source_width / source_height)), ideal_dimension)
    # Never upscale: past the original's size a bigger file adds bytes, not detail.
    one_x, two_x = (get_thumbnail(image, str(width * scale), format="PNG", upscale=False) for scale in (1, 2))
    if source_width > width:
        # sorl can land 1px off the requested width; drawing at the rendition's exact size
        # keeps 1x screens on the 1x file instead of fetching 2x.
        width, height = one_x.width, one_x.height
    else:
        height = round(width * source_height / source_width)
    renditions = {im.width: im.url for im in (one_x, two_x)}
    return {
        "src": one_x.url,
        "srcset": ", ".join(f"{url} {im_width}w" for im_width, url in renditions.items()),
        "width": width,
        "height": height,
    }
