"""Contract rendering utilities for generating sponsorship agreements as PDF and DOCX."""

import logging
import re
import tempfile
from pathlib import Path

import pypandoc
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.dateformat import format as date_format
from django.utils.http import content_disposition_header
from unidecode import unidecode

logger = logging.getLogger(__name__)

_dirname = Path(__file__).parent
DOCXPAGEBREAK_FILTER = str(_dirname / "pandoc_filters" / "pagebreak.py")
CONTRACT_SAFETY_FILTER = str(_dirname / "pandoc_filters" / "contract-safety.lua")
REFERENCE_DOCX = str(_dirname / "reference.docx")

# Disable raw TeX and TeX math so user input can't reach the LaTeX engine as commands
# or math. The template's own raw TeX uses raw_attribute (`...`{=latex}), which stays on.
CONTRACT_MARKDOWN_FORMAT = "markdown-raw_tex-tex_math_dollars-tex_math_single_backslash"

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# LaTeX reports e.g. "Unicode character 🐍 (U+1F40D)\nnot set up for use with LaTeX".
_UNSUPPORTED_CHARACTER_RE = re.compile(r"Unicode character (.+?) \(U\+([0-9A-Fa-f]+)\)")
_FILENAME_UNSAFE_RE = re.compile(r"[^A-Za-z0-9]+")


class ContractRenderError(RuntimeError):
    """Pandoc/LaTeX could not render the contract; ``str()`` is a message safe to show staff."""


def _convert_text(markdown, to, outputfile, extra_args):
    """Run pandoc, logging the real failure and raising a ContractRenderError that explains it."""
    try:
        pypandoc.convert_text(
            markdown, to, outputfile=outputfile, format=CONTRACT_MARKDOWN_FORMAT, extra_args=extra_args
        )
    except RuntimeError as exc:
        logger.exception("Contract %s rendering failed", to.upper())
        match = _UNSUPPORTED_CHARACTER_RE.search(str(exc))
        if match:
            msg = (
                f'The contract contains a character the PDF renderer cannot print: "{match.group(1)}" '
                f"(U+{match.group(2).upper()}). Remove it from the sponsor details, contacts or contract text "
                "and try again."
            )
        else:
            msg = f"The contract {to.upper()} could not be generated. The error has been logged."
        raise ContractRenderError(msg) from exc


def contract_filename(contract, extension):
    """Return an ASCII-only download/attachment filename for the contract."""
    prefix = "sponsorship-renewal" if contract.sponsorship.renewal else "sponsorship-contract"
    sponsor_slug = _FILENAME_UNSAFE_RE.sub("-", unidecode(contract.sponsorship.sponsor.name)).strip("-")[:80]
    return f"{prefix}-{sponsor_slug or 'sponsor'}.{extension}"


def _clean_split(text, separator="\n"):
    """Split text by newlines and strip dashes and whitespace from each part."""
    return [t.replace("-", "").strip() for t in text.split("\n") if t.replace("-", "").strip()]


def _contract_context(contract, **context):
    """Build the template context dictionary for rendering a contract."""
    start_date = contract.sponsorship.start_date
    context.update(
        {
            "contract": contract,
            "start_date": start_date,
            "start_day_english_suffix": date_format(start_date, "S"),
            "sponsor": contract.sponsorship.sponsor,
            "sponsorship": contract.sponsorship,
            "benefits": _clean_split(contract.benefits_list.raw),
            "legal_clauses": _clean_split(contract.legal_clauses.raw),
            "renewal": bool(contract.sponsorship.renewal),
        }
    )
    previous_effective = contract.sponsorship.previous_effective_date
    context["previous_effective"] = previous_effective or "UNKNOWN"
    context["previous_effective_english_suffix"] = (
        date_format(previous_effective, "S") if previous_effective else "UNKNOWN"
    )
    return context


def render_markdown_from_template(contract, **context):
    """Render the sponsorship agreement markdown template with contract data."""
    template = "sponsors/admin/contracts/sponsorship-agreement.md"
    context = _contract_context(contract, **context)
    return render_to_string(template, context)


def render_contract_to_pdf_response(request, contract, *, as_attachment=False, **context):
    """Return an HTTP response containing the contract rendered as a PDF (inline unless ``as_attachment``)."""
    response = HttpResponse(render_contract_to_pdf_file(contract, **context), content_type="application/pdf")
    response["Content-Disposition"] = content_disposition_header(as_attachment, contract_filename(contract, "pdf"))
    return response


def render_contract_to_pdf_file(contract, **context):
    """Convert the contract markdown to a PDF file and return its bytes."""
    with tempfile.NamedTemporaryFile(), tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
        markdown = render_markdown_from_template(contract, **context)
        _convert_text(markdown, "pdf", pdf_file.name, ["--sandbox", "--lua-filter", CONTRACT_SAFETY_FILTER])
        return pdf_file.read()


def render_contract_to_docx_response(request, contract, **context):
    """Return an HTTP response with the contract rendered as a DOCX download."""
    response = HttpResponse(render_contract_to_docx_file(contract, **context), content_type=DOCX_CONTENT_TYPE)
    response["Content-Disposition"] = content_disposition_header(True, contract_filename(contract, "docx"))  # noqa: FBT003
    return response


def render_contract_to_docx_file(contract, **context):
    """Convert the contract markdown to a DOCX file and return its bytes."""
    markdown = render_markdown_from_template(contract, **context)
    with tempfile.NamedTemporaryFile() as docx_file:
        _convert_text(
            markdown,
            "docx",
            docx_file.name,
            [
                "--sandbox",
                "--lua-filter",
                CONTRACT_SAFETY_FILTER,
                "--filter",
                DOCXPAGEBREAK_FILTER,
                "--reference-doc",
                REFERENCE_DOCX,
            ],
        )
        return docx_file.read()
