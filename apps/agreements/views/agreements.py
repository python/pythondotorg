"""Agreement review, downloads, and document editing."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.agreements import documents, workflow
from apps.agreements.auth import administrator_required, preparer_required
from apps.agreements.forms.contracts import EditDocumentForm
from apps.agreements.models import Agreement, CustomContract, SignedCopy
from apps.agreements.views.helpers import _agreement_or_404, _diff, action_forms, file_response

if TYPE_CHECKING:
    from uuid import UUID

    from django.forms import BaseForm
    from django.http import HttpRequest

    from apps.users.models import User

RECENT = 25


@preparer_required
def queue(request: HttpRequest) -> HttpResponse:
    """Every agreement that needs the PSF or the counterparty, then recent ones and custom drafts."""
    agreements = Agreement.objects.select_related("counterparty_account")
    return render(
        request,
        "agreements/queue.html",
        {
            "to_countersign": agreements.filter(status=Agreement.Status.SIGNED).order_by("signed_at"),
            "awaiting_signature": agreements.filter(status=Agreement.Status.OFFERED).order_by("offered_at"),
            "recent": agreements.exclude(status__in=[Agreement.Status.SIGNED, Agreement.Status.OFFERED])[:RECENT],
            "drafts": CustomContract.objects.filter(agreement__isnull=True),
            "nav": "queue",
        },
    )


@login_required
def detail(request: HttpRequest, pk: UUID, status: int = 200, **bound: BaseForm | None) -> HttpResponse:
    """Review an agreement and act on it."""
    agreement = _agreement_or_404(request, pk)
    html, metadata_hidden = documents.render_agreement_preview(documents.final_markdown(agreement))
    context = {
        **action_forms(request, agreement, **bound),
        "html": html,
        "metadata_hidden": metadata_hidden,
        "nav": "queue",
    }
    return render(request, "agreements/detail.html", context, status=status)


@login_required
def document(request: HttpRequest, pk: UUID, fmt: str) -> HttpResponse:
    """Download the agreement as PDF or DOCX, with any signatures so far."""
    agreement = _agreement_or_404(request, pk)
    if fmt not in documents.RENDERERS:
        raise Http404
    content = documents.RENDERERS[fmt](documents.final_markdown(agreement))
    return file_response(content, fmt, f"agreement-{agreement.reference}-{agreement.status}")


@login_required
def copy_download(request: HttpRequest, pk: UUID, kind: str) -> HttpResponse:
    """Download a signed copy kept with the agreement."""
    agreement = _agreement_or_404(request, pk)
    copy = get_object_or_404(SignedCopy, agreement=agreement, kind=kind)
    response = HttpResponse(bytes(copy.content), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="psf-agreement-{agreement.reference}-{kind}.pdf"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@administrator_required
def edit(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Edit one agreement's text before it is signed; every saved edit is a new revision."""
    agreement = _agreement_or_404(request, pk)
    if not agreement.is_editable:
        messages.error(request, "Only an agreement awaiting signature can be edited.")
        return redirect(agreement)
    initial = {"markdown": agreement.document_markdown, "base_sha256": agreement.document_sha256}
    form = EditDocumentForm(request.POST or None, initial=initial)
    preview = None
    conflict = None
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if "preview" in request.POST:
            preview, _ = documents.render_html(
                documents.preview_markdown(data["markdown"], agreement.counterparty_name)
            )
        else:
            try:
                workflow.edit(
                    agreement,
                    markdown=data["markdown"],
                    note=data["note"],
                    user=cast("User", request.user),
                    base_sha256=data["base_sha256"],
                )
            except workflow.DocumentChangedError:
                agreement.refresh_from_db()
                submitted = request.POST.copy()
                submitted["base_sha256"] = agreement.document_sha256
                form = EditDocumentForm(submitted)
                conflict = {
                    "current_markdown": agreement.document_markdown,
                    "diff": _diff(agreement.document_markdown, data["markdown"]),
                }
            except (workflow.InvalidTransitionError, ValueError) as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Saved as a new revision. Anyone signing now sees this text.")
                return redirect(agreement)
    revisions = list(agreement.revisions.select_related("created_by"))
    history = [
        {"revision": rev, "diff": _diff(older.markdown, rev.markdown) if older else None}
        for rev, older in zip(revisions, [*revisions[1:], None], strict=True)
    ]
    return render(
        request,
        "agreements/edit.html",
        {
            "agreement": agreement,
            "form": form,
            "preview": preview,
            "conflict": conflict,
            "history": history,
            "nav": "queue",
        },
        status=409 if conflict else (400 if form.errors else 200),
    )
