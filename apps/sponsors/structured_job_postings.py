"""Split-field widget + helpers for the sponsor job postings benefit.

Stores composed rows as pipe-delimited lines in the existing TextAsset
value. No new model or benefit type — this is purely a form-layer concern.

Lives in its own module so models/benefits.py can import the field at the
top without pulling in apps.sponsors.forms (circular).
"""

from django import forms

STRUCTURED_JOB_POSTINGS_BLANK_ROW_COUNT = 3
STRUCTURED_JOB_POSTINGS_MIN_VISIBLE_ROWS = 15
_TITLE_URL_PARTS = 2
_TITLE_LOCATION_URL_PARTS = 3


def parse_structured_job_postings(text):
    """Parse pipe-delimited job listing text into a list of row dicts.

    Expected format, one job per line:
        Title | Location | URL

    Location is optional (2 fields also accepted). Lines that don't match
    that shape are preserved as title-only rows so the sponsor can see
    (and fix) unrecognized content rather than silently losing it.
    """
    if not text:
        return []
    rows = []
    for raw_line in text.replace("\ufeff", "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == _TITLE_URL_PARTS:
            title, url = parts
            location = ""
        elif len(parts) == _TITLE_LOCATION_URL_PARTS:
            title, location, url = parts
        else:
            rows.append({"title": line, "location": "", "url": ""})
            continue
        rows.append({"title": title, "location": location, "url": url})
    return rows


def serialize_structured_job_postings(rows):
    """Compose a list of row dicts back into pipe-delimited text."""
    lines = []
    for row in rows:
        title = (row.get("title") or "").strip()
        location = (row.get("location") or "").strip()
        url = (row.get("url") or "").strip()
        if not title and not location and not url:
            continue
        parts = [title, location, url] if location else [title, url]
        lines.append(" | ".join(parts))
    return "\n".join(lines)


class StructuredJobPostingsWidget(forms.Widget):
    """Renders N rows of (title, location, url) inputs.

    Composes the rows into pipe-delimited text on submission, parses stored
    text back into rows on form init. Underlying TextAsset storage stays a
    single text field.
    """

    template_name = "sponsors/widgets/structured_job_postings.html"

    def format_value(self, value):
        """Parse the stored text into rows and pad with blanks for the form."""
        rows = parse_structured_job_postings(value)
        filled = len(rows)
        visible = max(
            STRUCTURED_JOB_POSTINGS_MIN_VISIBLE_ROWS,
            filled + STRUCTURED_JOB_POSTINGS_BLANK_ROW_COUNT,
        )
        rows.extend({"title": "", "location": "", "url": ""} for _ in range(visible - filled))
        return rows

    def get_context(self, name, value, attrs):
        """Expose the parsed rows to the widget template."""
        context = super().get_context(name, value, attrs)
        context["widget"]["rows"] = self.format_value(value)
        return context

    def value_from_datadict(self, data, files, name):
        """Read the per-row POST fields and compose them into pipe-delimited text."""
        titles = data.getlist(f"{name}__title")
        locations = data.getlist(f"{name}__location")
        urls = data.getlist(f"{name}__url")
        total = max(len(titles), len(locations), len(urls))
        rows = [
            {
                "title": titles[idx] if idx < len(titles) else "",
                "location": locations[idx] if idx < len(locations) else "",
                "url": urls[idx] if idx < len(urls) else "",
            }
            for idx in range(total)
        ]
        return serialize_structured_job_postings(rows)


class StructuredJobPostingsField(forms.CharField):
    """CharField backed by the structured job postings widget."""

    widget = StructuredJobPostingsWidget
