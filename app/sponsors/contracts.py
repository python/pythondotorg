import os
import tempfile

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.dateformat import format
from unidecode import unidecode

import pypandoc

dirname = os.path.dirname(__file__)
DOCXPAGEBREAK_FILTER = os.path.join(dirname, "pandoc_filters/pagebreak.py")
REFERENCE_DOCX = os.path.join(dirname, "reference.docx")


def _clean_split(text, separator="\n"):
    return [
        t.replace("-", "").strip()
        for t in text.split("\n")
        if t.replace("-", "").strip()
    ]


def _contract_context(contract, **context):
    start_date = contract.sponsorship.start_date
    context.update(
        {
            "contract": contract,
            "start_date": start_date,
            "start_day_english_suffix": format(start_date, "S"),
            "sponsor": contract.sponsorship.sponsor,
            "sponsorship": contract.sponsorship,
            "benefits": _clean_split(contract.benefits_list.raw),
            "legal_clauses": _clean_split(contract.legal_clauses.raw),
            "renewal": True if contract.sponsorship.renewal else False,
        }
    )
    previous_effective = contract.sponsorship.previous_effective_date
    context["previous_effective"] = previous_effective if previous_effective else "UNKNOWN"
    context["previous_effective_english_suffix"] = format(previous_effective, "S") if previous_effective else "UNKNOWN"
    return context


def render_markdown_from_template(contract, **context):
    template = "sponsors/admin/contracts/sponsorship-agreement.md"
    context = _contract_context(contract, **context)
    return render_to_string(template, context)


def render_contract_to_pdf_response(request, contract, **context):
    response = HttpResponse(
        render_contract_to_pdf_file(contract, **context), content_type="application/pdf"
    )
    return response


def render_contract_to_pdf_file(contract, **context):
    with tempfile.NamedTemporaryFile() as docx_file:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
            markdown = render_markdown_from_template(contract, **context)
            pdf = pypandoc.convert_text(
                markdown, "pdf", outputfile=pdf_file.name, format="md"
            )
            return pdf_file.read()


def render_contract_to_docx_response(request, contract, **context):
    response = HttpResponse(
        render_contract_to_docx_file(contract, **context),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response[
        "Content-Disposition"
    ] = f"attachment; filename={'sponsorship-renewal' if contract.sponsorship.renewal else 'sponsorship-contract'}-{unidecode(contract.sponsorship.sponsor.name.replace(' ', '-').replace('.', ''))}.docx"
    return response


def render_contract_to_docx_file(contract, **context):
    markdown = render_markdown_from_template(contract, **context)
    with tempfile.NamedTemporaryFile() as docx_file:
        docx = pypandoc.convert_text(
            markdown,
            "docx",
            outputfile=docx_file.name,
            format="md",
            filters=[DOCXPAGEBREAK_FILTER],
            extra_args=[f"--reference-doc", REFERENCE_DOCX],
        )
        return docx_file.read()
