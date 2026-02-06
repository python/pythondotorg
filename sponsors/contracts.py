"""Contract rendering utilities for generating sponsorship agreements as PDF and DOCX."""

import tempfile
from pathlib import Path

import pypandoc
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.dateformat import format as date_format
from unidecode import unidecode

_dirname = Path(__file__).parent
DOCXPAGEBREAK_FILTER = str(_dirname / "pandoc_filters" / "pagebreak.py")
REFERENCE_DOCX = str(_dirname / "reference.docx")


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
    context["previous_effective"] = previous_effective if previous_effective else "UNKNOWN"
    context["previous_effective_english_suffix"] = (
        date_format(previous_effective, "S") if previous_effective else "UNKNOWN"
    )
    return context


def render_markdown_from_template(contract, **context):
    """Render the sponsorship agreement markdown template with contract data."""
    template = "sponsors/admin/contracts/sponsorship-agreement.md"
    context = _contract_context(contract, **context)
    return render_to_string(template, context)


def render_contract_to_pdf_response(request, contract, **context):
    """Return an HTTP response containing the contract rendered as a PDF."""
    return HttpResponse(render_contract_to_pdf_file(contract, **context), content_type="application/pdf")


def render_contract_to_pdf_file(contract, **context):
    """Convert the contract markdown to a PDF file and return its bytes."""
    with tempfile.NamedTemporaryFile(), tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
        markdown = render_markdown_from_template(contract, **context)
        pypandoc.convert_text(markdown, "pdf", outputfile=pdf_file.name, format="md")
        return pdf_file.read()


def render_contract_to_docx_response(request, contract, **context):
    """Return an HTTP response with the contract rendered as a DOCX download."""
    response = HttpResponse(
        render_contract_to_docx_file(contract, **context),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = (
        f"attachment; filename={'sponsorship-renewal' if contract.sponsorship.renewal else 'sponsorship-contract'}-{unidecode(contract.sponsorship.sponsor.name.replace(' ', '-').replace('.', ''))}.docx"
    )
    return response


def render_contract_to_docx_file(contract, **context):
    """Convert the contract markdown to a DOCX file and return its bytes."""
    markdown = render_markdown_from_template(contract, **context)
    with tempfile.NamedTemporaryFile() as docx_file:
        pypandoc.convert_text(
            markdown,
            "docx",
            outputfile=docx_file.name,
            format="md",
            filters=[DOCXPAGEBREAK_FILTER],
            extra_args=["--reference-doc", REFERENCE_DOCX],
        )
        return docx_file.read()
