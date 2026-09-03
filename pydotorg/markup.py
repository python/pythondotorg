"""Sanitized markup renderers for MarkupField content.

django-markupfield marks the rendered markdown/RST output safe and templates
print it with ``|safe``. The bundled renderers preserve link schemes such as
``javascript:`` in hrefs, and the site sends no Content-Security-Policy, so an
unsafe scheme in a markup link would execute in the browser of anyone viewing
the page.

Each default renderer is wrapped so its HTML passes through ``nh3.clean`` with
an http/https/mailto URL-scheme allowlist (plus a tag/attribute allowlist)
before it is marked safe. Wiring this through ``MARKUP_FIELD_TYPES`` covers
every MarkupField (nominations, jobs, success stories, comments) at once.
"""

import nh3
from markupfield.markup import DEFAULT_MARKUP_TYPES

ALLOWED_TAGS = {
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "caption",
    "code",
    "col",
    "colgroup",
    "dd",
    "del",
    "div",
    "dl",
    "dt",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "img",
    "ins",
    "kbd",
    "li",
    "ol",
    "p",
    "pre",
    "s",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}

ALLOWED_ATTRIBUTES = {
    "*": {"class", "id", "title"},
    "a": {"href"},
    "img": {"src", "alt", "width", "height"},
    "td": {"align", "colspan", "rowspan"},
    "th": {"align", "colspan", "rowspan", "scope"},
}

ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def sanitize(html):
    """Drop links and attributes whose scheme/name is not allowlisted."""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
    )


def _sanitizing(render):
    def sanitizing_render(markup):
        return sanitize(render(markup))

    return sanitizing_render


MARKUP_FIELD_TYPES = [(name, _sanitizing(render), *rest) for name, render, *rest in DEFAULT_MARKUP_TYPES]
