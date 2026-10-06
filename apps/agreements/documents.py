"""Render agreements and published terms as markdown, HTML, PDF, and DOCX.

A document's markdown carries two placeholders, ``SIGNATURES`` and ``EFFECTIVE_DATE``, that are
filled in when it is rendered; everything else is the text the counterparty signs, and its
SHA-256 identifies it. User input must go through ``md()``. Documents may be written by PSF
staff, so pandoc runs sandboxed with raw output disabled and a filter that rejects images.
"""

from __future__ import annotations

import hashlib
import re
import string
import tempfile
from datetime import UTC
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pypandoc
from django.utils import timezone
from django.utils.dateformat import format as date_format
from unidecode import unidecode

from pydotorg.markup import sanitize

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from datetime import datetime

    from apps.agreements.models import Agreement, TermsVersion

FILTER = str(Path(__file__).parent / "pandoc_filters" / "agreement.lua")
PANDOC_ARGS = ("--sandbox",)

# Documents are escaped or staff-written; these extensions are off as a second layer so
# nothing in a document can reach the LaTeX engine or the page as raw markup.
MARKDOWN_FORMAT = "markdown-raw_tex-raw_html-raw_attribute-tex_math_dollars-tex_math_single_backslash"

SIGNATURES = "AGREEMENTSIGNATURES"
EFFECTIVE_DATE = "AGREEMENTEFFECTIVEDATE"
PAGEBREAK = "::: pagebreak\n:::"

PROVIDER_NAME = "Python Software Foundation"
PROVIDER_PREAMBLE = (
    "**PYTHON SOFTWARE FOUNDATION**, a Delaware nonprofit corporation and tax-exempt organization "
    "under Section 501(c)(3) of the Internal Revenue Code (EIN 04-3594598), with its principal place "
    "of business at 9450 SW Gemini Drive, ECM \\#90772, Beaverton, OR 97008 "
    '(the "Provider" or the "PSF")'
)

_PUNCTUATION = re.compile(f"([{re.escape(string.punctuation)}])")
_H2 = re.compile(r'<h2 id="([^"]+)">(.*?)</h2>', re.DOTALL)
_TAGS = re.compile(r"<[^>]+>")
_LEGACY_TERMS_FINGERPRINT = re.compile(
    r"(?P<citation>published at <https?://[^>\n]+>), SHA-256 "
    r"(?:`[a-f0-9]{64}`|[a-f0-9]{16}(?: [a-f0-9]{16}){3})(?=\.)"
)
_LEGACY_FINGERPRINT_DESCRIPTION = re.compile(r"(?<=identified by its permanent address) and SHA\\?-256 hash(?=\.)")


def md(value: object) -> str:
    """Escape user-supplied text so pandoc renders it literally, on a single line."""
    return _PUNCTUATION.sub(r"\\\1", " ".join(str(value).split()))


def sha256(text: str) -> str:
    """Hash ``text`` with SHA-256 and return the hex digest."""
    return hashlib.sha256(text.encode()).hexdigest()


def date(value: datetime | None) -> str:
    """Format a datetime as a long local date."""
    return date_format(timezone.localtime(value), "F j, Y")


def _utc(value: datetime) -> str:
    return f"{value.astimezone(UTC):%Y-%m-%d %H:%M:%S} UTC"


def table(
    header: tuple[str, str],
    rows: Iterable[tuple[str, str]],
    *,
    widths: tuple[int, int] = (28, 52),
    amounts: bool = False,
) -> list[str]:
    """Return a two-column pipe table; cells are already escaped markdown.

    Pandoc sets a table full width, in the proportions of the separator row, only when a source
    line exceeds 72 characters; the separator is always longer, so every table lines up.
    """
    right = ":" if amounts else ""
    separator = f"|:{'-' * widths[0]}|{'-' * widths[1]}{right}|"
    out = [f"| {header[0]} | {header[1]} |", separator]
    return [*out, *(f"| {label} | {value} |" for label, value in rows), ""]


def amounts_table(header: tuple[str, str], rows: Iterable[tuple[str, str]]) -> list[str]:
    """Return a table whose second column holds right-aligned amounts."""
    return table(header, rows, widths=(56, 24), amounts=True)


# ---------- Signatures ----------


def _signature_column(name: str, title: str, when: datetime | None, *, on_file: bool = False) -> list[str]:
    blank = "\\_" * 18
    if not when:
        return [f"By: {blank}", "Name:", "Title:", "Date:"]
    by = "Signed copy on file" if on_file else f"*/s/ {md(name)}*"
    return [f"By: {by}", f"Name: {md(name)}", f"Title: {md(title)}", f"Date: {date(when)}"]


def signature_table(
    counterparty_name: str, psf: Sequence[str] | None = None, counterparty: Sequence[str] | None = None
) -> str:
    """Two signature columns; ``psf`` and ``counterparty`` are ``_signature_column`` rows, or blank."""
    psf = psf or _signature_column("", "", None)
    counterparty = counterparty or _signature_column("", "", None)
    rows = [
        f"| **{PROVIDER_NAME.upper()}** | **{md(counterparty_name.upper())}** |",
        "|:------------------------------------|:------------------------------------|",
    ]
    rows += [f"| {p} | {c} |" for p, c in zip(psf, counterparty, strict=True)]
    return "\n".join(rows)


def preview_markdown(markdown: str, counterparty_name: str) -> str:
    """Fill a draft's placeholders with blank signature lines."""
    return markdown.replace(SIGNATURES, signature_table(counterparty_name)).replace(
        EFFECTIVE_DATE, "The date of the last signature below."
    )


def _signature_record(agreement: Agreement) -> list[str]:
    copies = set(agreement.signed_copies.values_list("kind", flat=True))
    rows = [
        ("Reference", agreement.reference),
        ("Document", f"{agreement.title}, revision {agreement.revision}"),
    ]
    rows += [
        (f"Terms: {version.terms.title}", f"Version {version.version}")
        for version in agreement.terms_versions.select_related("terms")
    ]
    rows.append(("Signatory", f"{agreement.signer_name}, {agreement.signer_title} ({agreement.signer_email})"))
    if agreement.signature_method == agreement.SignatureMethod.OFFLINE:
        intro = (
            f"{md(agreement.counterparty_name)} signed a copy of this document outside python.org. "
            "The signed copy is kept with the agreement."
        )
        rows.append(("Signed", f"{date(agreement.signed_at)}, outside python.org"))
        rows.append(("Signed copy", "On file"))
    else:
        how = (
            "an emailed signing link" if agreement.signature_method == agreement.SignatureMethod.LINK else "an account"
        )
        intro = f"{md(agreement.counterparty_name)} signed this document on python.org with {how}."
        rows.append(("Signed", _utc(cast("datetime", agreement.signed_at))))
    if agreement.countersigned_at:
        rows.append(("PSF signatory", f"{agreement.countersigner_name}, {agreement.countersigner_title}"))
        rows.append(("PSF signed", _utc(agreement.countersigned_at)))
    if "executed" in copies:
        rows.append(("Countersigned copy", "On file"))
    record = table(("Field", "Value"), [(md(label), md(value)) for label, value in rows], widths=(30, 50))
    return [PAGEBREAK, "", "## Signature Record", "", intro, "", *record]


def final_markdown(agreement: Agreement) -> str:
    """Return an offered agreement's document with its signatures and signature record filled in."""
    on_file = agreement.signature_method == agreement.SignatureMethod.OFFLINE
    psf = counterparty = None
    if agreement.countersigned_at:
        psf = _signature_column(agreement.countersigner_name, agreement.countersigner_title, agreement.countersigned_at)
    if agreement.signed_at:
        counterparty = _signature_column(
            agreement.signer_name, agreement.signer_title, agreement.signed_at, on_file=on_file
        )
    effective = (
        date(agreement.countersigned_at) if agreement.countersigned_at else "The date of the last signature below."
    )
    text = agreement.document_markdown.replace(
        SIGNATURES, signature_table(agreement.counterparty_name, psf, counterparty)
    ).replace(EFFECTIVE_DATE, effective)
    if agreement.signed_at:
        text += "\n" + "\n".join(_signature_record(agreement))
    return text


def terms_download_markdown(version: TermsVersion) -> str:
    """Return a published terms version with a title block, for PDF and DOCX downloads."""
    terms = version.terms
    header = [f"# {terms.title}", ""]
    if terms.under_review:
        header += ["**DRAFT — For Attorney Review**", ""]
    header += [f"*Version {md(version.version)}, published at <{version.permanent_url}>*", ""]
    return "\n".join([*header, version.markdown])


# ---------- Rendering ----------


def _convert(markdown: str | bytes, to: str, outputfile: str | None = None, extra_args: Iterable[str] = ()) -> str:
    return pypandoc.convert_text(
        markdown,
        to,
        format=MARKDOWN_FORMAT,
        outputfile=outputfile,
        filters=[FILTER],
        extra_args=[*PANDOC_ARGS, *extra_args],
    )


@lru_cache(maxsize=32)
def _html(markdown: str | bytes) -> str:
    return sanitize(_convert(markdown, "html5"))


def _toc_title(title: str) -> str:
    """Lower-case exhibit headings, which the terms set in capitals, for the contents list."""
    if not title.isupper():
        return title
    label, _, rest = title.partition(" — ")
    return f"{label.title()} — {rest.capitalize()}" if rest else title.title()


def render_html(markdown: str | bytes) -> tuple[str, list[tuple[str, str]]]:
    """Render markdown to sanitized HTML plus a table of contents of its sections."""
    html = _html(markdown)
    toc = [(anchor, _toc_title(" ".join(_TAGS.sub("", title).split()))) for anchor, title in _H2.findall(html)]
    return html, toc


def render_agreement_preview(markdown: str) -> tuple[str, bool]:
    """Hide generated legacy fingerprint metadata in HTML, never in stored text or downloads."""
    preview = _LEGACY_TERMS_FINGERPRINT.sub(r"\g<citation>", markdown)
    preview = _LEGACY_FINGERPRINT_DESCRIPTION.sub("", preview)
    html, _ = render_html(preview)
    return html, preview != markdown


def _convert_file(markdown: str | bytes, to: str, suffix: str, extra_args: Iterable[str] = ()) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=suffix) as out:
        _convert(markdown, to, outputfile=out.name, extra_args=extra_args)
        return Path(out.name).read_bytes()


# pdflatex (the only TeX engine in the image) sets Latin-1, Latin Extended-A, and common typography.
_PDFLATEX_LAST_NATIVE = 0x17F
_PDFLATEX_EXTRA = frozenset("‘’‚“”„–—…•€×·§¶†‡‰")  # noqa: RUF001 - typographic characters pdflatex can set


def _pdflatex_safe(markdown: str) -> str:
    """Transliterate characters pdflatex can't set, so a counterparty's name never breaks the PDF.

    Only the PDF rendering changes; HTML, DOCX, and the signed snapshot keep the exact text.
    """

    def replace(char: str) -> str:
        if ord(char) <= _PDFLATEX_LAST_NATIVE or char in _PDFLATEX_EXTRA:
            return char
        return _PUNCTUATION.sub(r"\\\1", unidecode(char)) or "?"

    return "".join(replace(char) for char in markdown)


@lru_cache(maxsize=16)
def render_pdf(markdown: str) -> bytes:
    """Render markdown to PDF bytes."""
    return _convert_file(
        _pdflatex_safe(markdown),
        "pdf",
        ".pdf",
        ["-V", "geometry:margin=1in", "-V", "fontsize=11pt", "-V", "linkcolor=black"],
    )


@lru_cache(maxsize=16)
def render_docx(markdown: str | bytes) -> bytes:
    """Render markdown to DOCX bytes."""
    return _convert_file(markdown, "docx", ".docx")


RENDERERS: dict[str, Callable[[str], bytes]] = {"pdf": render_pdf, "docx": render_docx}
CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
