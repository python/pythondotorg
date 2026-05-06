"""Custom template tags and filters for the pages app."""

import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.text import slugify

register = template.Library()

# Match h1–h4 elements; capture tag name, existing attributes, and inner HTML.
# Using DOTALL so inner content can span multiple lines.
_HEADING_RE = re.compile(r"<(h[1-4])([^>]*)>(.*?)</\1>", re.IGNORECASE | re.DOTALL)

# Extract the value of an existing id attribute, e.g. id="my-section".
_EXISTING_ID_RE = re.compile(r'\bid\s*=\s*["\'](.*?)["\']', re.IGNORECASE)


@register.filter(is_safe=True)
def add_heading_anchors(html):
    """Add self-link anchors to h1\u2013h4 headings.

    Given the rendered HTML of a CMS page, this filter finds every ``<h1>``,
    ``<h2>``, ``<h3>``, and ``<h4>`` element and injects a pilcrow (\u00b6)
    anchor inside it so visitors can copy a direct link to any section.

    Two cases are handled:

    * **Heading already has an ``id``** (common for RST-generated content where
      docutils injects ids automatically): the existing id is reused as the
      anchor target and a pilcrow link is appended.  The heading is otherwise
      left intact.
    * **Heading has no ``id``**: a URL-safe id is derived from the heading's
      plain text via :func:`django.utils.text.slugify`, a ``-N`` suffix is
      appended for duplicates, and both the id and the pilcrow link are added.

    Headings whose text produces an empty slug *and* that carry no existing id
    are left completely untouched.  The filter is idempotent: headings that
    already contain a ``headerlink`` anchor are skipped.

    Usage in a template::

        {% load page_tags %}
        {{ page.content|add_heading_anchors }}
    """
    seen_slugs: dict[str, int] = {}

    def _replace(match: re.Match) -> str:
        tag = match.group(1).lower()
        attrs = match.group(2)
        inner = match.group(3)

        # Idempotency: skip headings that already have a pilcrow link.
        if "headerlink" in inner:
            return match.group(0)

        # If the heading already carries an id (e.g. from RST/docutils),
        # reuse it for the pilcrow link rather than skipping the heading.
        existing = _EXISTING_ID_RE.search(attrs)
        if existing:
            anchor_id = existing.group(1)
            link = (
                f'<a class="headerlink" href="#{anchor_id}" '
                f'title="Link to this section" aria-label="Link to this section">\u00b6</a>'
            )
            return f'<{tag}{attrs}>{inner} {link}</{tag}>'

        # Derive a slug from the plain text (strip any nested HTML tags).
        plain_text = re.sub(r"<[^>]+>", "", inner).strip()
        base_slug = slugify(plain_text)

        if not base_slug:
            return match.group(0)

        # Deduplicate: first occurrence keeps the bare slug; subsequent
        # occurrences become slug-2, slug-3, ...
        count = seen_slugs.get(base_slug, 0) + 1
        seen_slugs[base_slug] = count
        anchor_id = base_slug if count == 1 else f"{base_slug}-{count}"

        link = (
            f'<a class="headerlink" href="#{anchor_id}" '
            f'title="Link to this section" aria-label="Link to this section">\u00b6</a>'
        )
        return f'<{tag} id="{anchor_id}"{attrs}>{inner} {link}</{tag}>'

    return mark_safe(_HEADING_RE.sub(_replace, str(html)))
