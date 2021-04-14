"""
This module is a wrapper around django-easy-pdf so we can reuse code
"""
from easy_pdf.rendering import render_to_pdf_response, render_to_pdf

from markupfield_helpers.helpers import render_md
from django.utils.html import mark_safe


def _clean_split(text, separator='\n'):
    return [
        t.replace('-', '').strip()
        for t in text.split('\n')
        if t.replace('-', '').strip()
    ]


def _contract_context(contract, **context):
    context.update({
        "contract": contract,
        "start_date": contract.sponsorship.start_date,
        "sponsor": contract.sponsorship.sponsor,
        "sponsorship": contract.sponsorship,
        "benefits": _clean_split(contract.benefits_list.raw),
        "legal_clauses": _clean_split(contract.legal_clauses.raw),
    })
    return context


def render_contract_to_pdf_response(request, contract, **context):
    template = "sponsors/admin/preview-contract.html"
    context = _contract_context(contract, **context)
    from django.shortcuts import render
    #return render(request, template, context)
    return render_to_pdf_response(request, template, context)


def render_contract_to_pdf_file(contract, **context):
    template = "sponsors/admin/preview-contract.html"
    context = _contract_context(contract, **context)
    return render_to_pdf(template, context)
