"""Utility functions for success stories migration data conversion.

The following functions are created for
successstories/migrations/0006_auto_20170726_0824.py:

* convert_to_datetime()
* get_field_list()
"""

import datetime
from xml.etree.ElementTree import fromstring

from django.utils.timezone import get_current_timezone
from docutils.core import publish_doctree


def convert_to_datetime(string):
    """Parse a date string into a timezone-aware datetime, trying multiple formats."""
    formats = [
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(string, fmt).replace(tzinfo=get_current_timezone())
        except ValueError:
            continue
    return None


def get_field_list(source):
    """Extract field name-value pairs from a reStructuredText document source."""
    dom = publish_doctree(source).asdom()
    tree = fromstring(dom.toxml())  # noqa: S314 - parsing our own docutils output, not untrusted XML
    for field in tree.iter():
        if field.tag == "field":
            name = next(field.iter(tag="field_name"))
            body = next(field.iter(tag="field_body"))
            yield name.text.lower(), "".join(body.itertext())
        elif field.tag in ("author", "date"):
            yield field.tag, "".join(field.itertext())
