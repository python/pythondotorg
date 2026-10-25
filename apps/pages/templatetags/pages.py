"""Template filters for rendering CMS page content."""

import re
from collections import Counter

from dateutil import parser as date_parser
from django import template
from django.utils.html import mark_safe

register = template.Library()

_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?"
# A board resolution is a <blockquote> followed by a paragraph with its vote date, e.g.
# "Approved; 9-0-1, 2026-08-12", "Declined 3-4-0, December 2, 2014", "September 4, 2018".
_RESOLUTION_RE = re.compile(
    r"<blockquote>(?P<body>(?:(?!<blockquote>).)*?</blockquote>\s*<p>[^<]*?)"
    rf"(?P<date>\d{{4}}-\d\d-\d\d|{_MONTH}\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}\s+{_MONTH},?\s+\d{{4}})",
    re.DOTALL,
)


@register.filter
def resolution_anchors(content):
    """Anchor each board resolution at its vote date and turn that date into a link to it.

    Ids are ISO dates; later resolutions on the same date get ``-2``, ``-3``, ... in page order.
    """
    seen = Counter()

    def anchor(match):
        try:
            date = date_parser.parse(match["date"]).date().isoformat()
        except ValueError:
            return match[0]
        seen[date] += 1
        anchor_id = date if seen[date] == 1 else f"{date}-{seen[date]}"
        return f'<blockquote id="{anchor_id}">{match["body"]}<a href="#{anchor_id}">{match["date"]}</a>'

    return mark_safe(_RESOLUTION_RE.sub(anchor, str(content)))  # noqa: S308
