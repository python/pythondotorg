"""View helpers shared by agreement pages and domain apps."""

import difflib

from allauth.account.adapter import get_adapter
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from apps.agreements import documents, workflow
from apps.agreements.auth import can_prepare, is_administrator
from apps.agreements.forms.signing import CountersignForm, DeclineForm, SignedCopyForm, SignForm, SigningLinkForm
from apps.agreements.models import Agreement


def signature_of(request, form):
    """Build an online ``Signature`` from a valid ``SignForm``."""
    return workflow.Signature(
        name=form.cleaned_data["signer_name"],
        title=form.cleaned_data["signer_title"],
        email=request.user.email,
        ip=get_adapter().get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
    )


def action_forms(request, agreement, **bound):
    """Return the forms ``agreements/_actions.html`` shows to this user, bound ones taking precedence."""
    user = request.user
    administrator = is_administrator(user)
    seen = {"document_sha256": agreement.document_sha256}
    forms = {}
    if agreement.status == Agreement.Status.OFFERED:
        if agreement.is_counterparty(user):
            forms["sign_form"] = SignForm(initial={**seen, "signer_name": user.get_full_name()})
        if administrator or agreement.is_counterparty(user):
            forms["copy_form"] = SignedCopyForm(initial=seen)
        if administrator:
            forms["link_form"] = SigningLinkForm()
    elif agreement.status == Agreement.Status.SIGNED and administrator:
        forms["countersign_form"] = CountersignForm(initial={"name": user.get_full_name()})
        forms["decline_form"] = DeclineForm()
    forms.update({name: form for name, form in bound.items() if form is not None})
    return {
        **forms,
        "agreement": agreement,
        "can_prepare": can_prepare(user),
        "is_administrator": administrator,
        "can_withdraw": agreement.status == Agreement.Status.OFFERED
        and (administrator or agreement.is_counterparty(user)),
        "copies": agreement.signed_copies.defer("content").select_related("uploaded_by"),
        "links": agreement.signing_links.all() if administrator else (),
    }


def _agreement_or_404(request, pk):
    agreement = get_object_or_404(Agreement.objects.select_related("counterparty_account"), pk=pk)
    if not agreement.can_view(request.user):
        raise Http404
    return agreement


def file_response(content, fmt, filename):
    """Return a PSF-prefixed PDF or DOCX download that caches must not keep."""
    response = HttpResponse(content, content_type=documents.CONTENT_TYPES[fmt])
    response["Content-Disposition"] = f'attachment; filename="psf-{filename}.{fmt}"'
    response["Cache-Control"] = "private, no-store"
    return response


def _diff(old, new):
    """Unified diff lines, each tagged ``add``, ``del``, ``hunk``, or ``""`` for context."""
    tags = {"+": "add", "-": "del", "@": "hunk"}
    lines = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=2)
    return [(tags.get(line[:1], ""), line) for line in list(lines)[2:]]
