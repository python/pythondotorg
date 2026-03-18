"""Custom template tags and filters for the pages app."""

import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.text import slugify

register = template.Library()

# Match h2–h4 elements; capture tag name, existing attributes, and inner HTML.
# Using DOTALL so inner content can span multiple lines.
_HEADING_RE = re.compile(r"<(h[2-4])([^>]*)>(.*?)</\1>", re.IGNORECASE | re.DOTALL)


@register.filter(is_safe=True)
def add_heading_anchors(html):
    """Add ``id`` attributes and self-link anchors to h2–h4 headings.

    Given the rendered HTML of a CMS page, this filter finds every ``<h2>``,
    ``<h3>``, and ``<h4>`` element and:

    1. Derives a URL-safe ``id`` from the heading's plain text (via
       :func:`django.utils.text.slugify`).
    2. Appends a ``-N`` suffix when the same slug appears more than once on
       the page, preventing duplicate ``id`` values.
    3. Injects a pilcrow (¶) anchor *inside* the heading so visitors can
       copy a direct link to any section.

    The filter is safe to apply to any page — headings that already carry an
    ``id`` attribute are left untouched, and headings whose text produces an
    empty slug are also skipped.

    Usage in a template::

        {% load page_tags %}
        {{ page.content|add_heading_anchors }}
    """
    seen_slugs: dict[str, int] = {}

    def _replace(match: re.Match) -> str:
        tag = match.group(1).lower()
        attrs = match.group(2)
        inner = match.group(3)

        # Skip headings that already have an id attribute.
        if re.search(r'\bid\s*=', attrs, re.IGNORECASE):
            return match.group(0)

        # Derive a slug from the plain text (strip any nested HTML tags).
        plain_text = re.sub(r"<[^>]+>", "", inner).strip()
        base_slug = slugify(plain_text)

        if not base_slug:
            return match.group(0)

        # Deduplicate: first occurrence keeps the bare slug; subsequent
        # occurrences become slug-2, slug-3, …
        count = seen_slugs.get(base_slug, 0) + 1
        seen_slugs[base_slug] = count
        anchor_id = base_slug if count == 1 else f"{base_slug}-{count}"

        link = (
            f'<a class="headerlink" href="#{anchor_id}" '
            f'title="Link to this section" aria-label="Link to this section">¶</a>'
        )
        return f'<{tag} id="{anchor_id}"{attrs}>{inner} {link}</{tag}>'

    return mark_safe(_HEADING_RE.sub(_replace, str(html)))
