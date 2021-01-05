"""
This module is a wrapper around django-easy-pdf so we can reuse code
"""
from easy_pdf.rendering import render_to_pdf_response, render_to_pdf

from markupfield_helpers.helpers import render_md
from django.utils.html import mark_safe


def _contract_context(contract, **context):
    # footnotes only work if in same markdown text as the references
    text = f"{contract.benefits_list.raw}\n\n**Legal Clauses**\n{contract.legal_clauses.raw}"
    html = render_md(text)
    context.update(
        {
            "contract": contract,
            "benefits_and_clauses": mark_safe(html),
        }
    )
    return context


def render_contract_to_pdf_response(request, contract, **context):
    template = "sponsors/admin/preview-contract.html"
    context = _contract_context(contract, **context)
    return render_to_pdf_response(request, template, context)


def render_contract_to_pdf_file(contract, **context):
    template = "sponsors/admin/preview-contract.html"
    context = _contract_context(contract, **context)
    return render_to_pdf(template, context)
