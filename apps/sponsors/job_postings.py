"""One-job-per-row form input for the sponsor job listings benefit.

Sponsors enter each job (title, optional location, link) as its own row. The
rows are stored in the benefit's existing ``TextAsset`` value, one job per line::

    Senior Python Engineer | Remote | https://example.com/jobs/1
    Developer Advocate | https://example.com/jobs/2

PyCon-site's sponsor sync parses that format into structured job postings.

Kept out of ``apps.sponsors.forms`` so ``models/benefits.py`` can import it
without a circular import.
"""

import re

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

SEPARATOR = "|"
ROW_PARTS = ("title", "location", "url")
HELP_TEXT = (
    "Enter one job per row: the job title, its location (optional), and a link to the job posting. "
    "Use “Add another job” for more rows. Clear a row to remove that job."
)

_MARKDOWN_LINK_RE = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>[^)\s]+)\)")
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_LEGACY_TITLE_STRIP = " \t-*:|,–—"  # noqa: RUF001 - en/em dashes used as markdown separators
_url_validator = URLValidator(schemes=["http", "https"])


def is_job_postings_asset(internal_name):
    """Return True if a required text asset collects sponsor job postings.

    Matches ``settings.SPONSOR_JOB_POSTINGS_ASSET_MARKERS`` against the internal
    name, ignoring case and ``_``/``-`` differences, so yearly clones
    (``pycon-2026-job-listing``) keep matching.
    """
    normalized = internal_name.lower().replace("_", "-")
    return any(marker.lower().replace("_", "-") in normalized for marker in settings.SPONSOR_JOB_POSTINGS_ASSET_MARKERS)


def _row(title="", location="", url=""):
    return {"title": title, "location": location, "url": url}


def _single_line(value):
    """Collapse whitespace, including every ``str.splitlines()`` boundary, to single spaces.

    Each job must serialize to exactly one stored line.
    """
    return " ".join(value.split())


def _lowercase_scheme(url):
    scheme, sep, rest = url.partition("://")
    return f"{scheme.lower()}{sep}{rest}"


def _parse_line(line):
    parts = [part.strip() for part in line.split(SEPARATOR)]
    if len(parts) in (2, 3) and _URL_RE.fullmatch(parts[-1]):
        return _row(parts[0], parts[1] if len(parts) == 3 else "", parts[-1])  # noqa: PLR2004

    # Legacy free-form markdown: recover what we can so the sponsor only has to tidy up.
    if match := _MARKDOWN_LINK_RE.search(line):
        return _row(match["title"].strip(), url=match["url"])
    if match := _URL_RE.search(line):
        title = (line[: match.start()] + line[match.end() :]).strip(_LEGACY_TITLE_STRIP)
        return _row(title, url=match.group().rstrip(".,;)"))
    return _row(line.strip(_LEGACY_TITLE_STRIP))


def parse_job_postings(text):
    """Split stored job postings text into row dicts, one per non-blank line.

    Lines in the ``Title | Location | URL`` (or ``Title | URL``) format parse
    exactly. Legacy markdown lines keep their link and text so nothing a
    sponsor already submitted disappears from the form.
    """
    if not text:
        return []
    rows = (_parse_line(line.strip()) for line in text.replace("\ufeff", "").splitlines())
    return [row for row in rows if any(row.values())]


def serialize_job_postings(rows):
    """Join row dicts into the stored one-job-per-line text."""
    lines = []
    for row in rows:
        parts = [row["title"], row["location"], row["url"]] if row["location"] else [row["title"], row["url"]]
        lines.append(f" {SEPARATOR} ".join(parts))
    return "\n".join(lines)


class JobPostingsWidget(forms.Widget):
    """Render one (title, location, link) row per job plus a blank row to add another."""

    template_name = "sponsors/widgets/job_postings.html"

    class Media:
        """Script that adds and removes rows in the browser."""

        js = ("js/sponsors/jobPostings.js",)

    def format_value(self, value):
        """Return the rows to render: stored or submitted jobs, then one blank row."""
        rows = parse_job_postings(value) if value is None or isinstance(value, str) else list(value)
        return [*rows, _row()]

    def value_from_datadict(self, data, files, name):
        """Collect the submitted rows, dropping rows left completely blank."""
        getter = getattr(data, "getlist", data.get)
        columns = []
        for part in ROW_PARTS:
            values = getter(f"{name}__{part}") or []
            columns.append([values] if isinstance(values, str) else values)
        rows = []
        for index in range(max(len(column) for column in columns)):
            row = _row(*(_single_line(column[index] if index < len(column) else "") for column in columns))
            if any(row.values()):
                rows.append(row)
        return rows

    def id_for_label(self, id_):
        """Point the field label at the first row's title input."""
        return f"{id_}_0_title" if id_ else id_


class JobPostingsField(forms.Field):
    """Validate job rows and return them as the stored one-job-per-line text."""

    widget = JobPostingsWidget

    def to_python(self, value):
        """Accept stored text (initial value) or the widget's list of rows."""
        if not value:
            return []
        if isinstance(value, str):
            return parse_job_postings(value)
        return list(value)

    def validate(self, value):
        """Require a title and a valid http(s) link for every job."""
        super().validate(value)
        errors = []
        for number, row in enumerate(value, start=1):
            if not row["title"]:
                errors.append(ValidationError("Job %(number)s: enter the job title.", params={"number": number}))
            if not row["url"]:
                errors.append(
                    ValidationError("Job %(number)s: enter a link to the job posting.", params={"number": number})
                )
            else:
                try:
                    _url_validator(row["url"])
                except ValidationError:
                    errors.append(
                        ValidationError(
                            "Job %(number)s: enter a full link starting with http:// or https://.",
                            params={"number": number},
                        )
                    )
            if any(SEPARATOR in row[part] for part in ROW_PARTS):
                errors.append(
                    ValidationError(
                        "Job %(number)s: remove the “%(separator)s” character.",
                        params={"number": number, "separator": SEPARATOR},
                    )
                )
        if errors:
            raise ValidationError(errors)

    def clean(self, value):
        """Return the validated rows as stored text, with lowercase link schemes."""
        rows = super().clean(value)
        return serialize_job_postings([{**row, "url": _lowercase_scheme(row["url"])} for row in rows])
