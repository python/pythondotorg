"""
This module is a wrapper around django-easy-pdf so we can reuse code
"""
import io
import os
from django.conf import settings
from django.http import HttpResponse
from django.utils.dateformat import format

from docxtpl import DocxTemplate
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
    start_date = contract.sponsorship.start_date
    context.update({
        "contract": contract,
        "start_date": start_date,
        "start_day_english_suffix": format(start_date, "S"),
        "sponsor": contract.sponsorship.sponsor,
        "sponsorship": contract.sponsorship,
        "benefits": _clean_split(contract.benefits_list.raw),
        "legal_clauses": _clean_split(contract.legal_clauses.raw),
    })
    return context


def render_contract_to_pdf_response(request, contract, **context):
    template = "sponsors/admin/preview-contract.html"
    context = _contract_context(contract, **context)
    return render_to_pdf_response(request, template, context)


def render_contract_to_pdf_file(contract, **context):
    template = "sponsors/admin/preview-contract.html"
    context = _contract_context(contract, **context)
    return render_to_pdf(template, context)


def _gen_docx_contract(output, contract, **context):
    template = os.path.join(settings.TEMPLATES_DIR, "sponsors", "admin", "contract-template.docx")
    doc = DocxTemplate(template)
    context = _contract_context(contract, **context)
    doc.render(context)
    doc.save(output)
    return output


def render_contract_to_docx_response(request, contract, **context):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename=contract.docx'
    return _gen_docx_contract(output=response, contract=contract, **context)


def render_contract_to_docx_file(contract, **context):
    fp = io.BytesIO()
    fp = _gen_docx_contract(output=fp, contract=contract, **context)
    fp.seek(0)
    return fp.read()
