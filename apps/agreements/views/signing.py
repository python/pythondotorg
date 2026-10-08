"""Signing actions and one-time invitation links."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from allauth.account.adapter import get_adapter
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.agreements import documents, notifications, workflow
from apps.agreements.auth import administrator_required, can_prepare, is_administrator
from apps.agreements.forms.signing import CountersignForm, DeclineForm, SignedCopyForm, SignForm, SigningLinkForm
from apps.agreements.models import Agreement, SigningLink
from apps.agreements.views.agreements import detail
from apps.agreements.views.helpers import _agreement_or_404, file_response, signature_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from uuid import UUID

    from django.http import HttpRequest, HttpResponse

    from apps.users.models import User

    class _TrackingRequest(HttpRequest):
        disable_tracking: bool


logger = logging.getLogger(__name__)


def _subject_url(request: HttpRequest, agreement: Agreement) -> str:
    if agreement.kind == "custom" and not can_prepare(request.user):
        return agreement.get_absolute_url()
    return agreement.subject_url


def _back(request: HttpRequest, agreement: Agreement) -> HttpResponse:
    target = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(target)
    return redirect(_subject_url(request, agreement))


def _run(request: HttpRequest, agreement: Agreement, action: Callable[[], object], success: str) -> bool:
    """Run a workflow action, turning a refused transition into a message."""
    try:
        action()
    except workflow.InvalidTransitionError as exc:
        messages.error(request, str(exc))
        return False
    messages.success(request, success)
    return True


@login_required
@require_POST
def sign(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Sign on python.org as the counterparty's account."""
    agreement = _agreement_or_404(request, pk)
    if not agreement.is_counterparty(request.user):
        raise Http404
    form = SignForm(request.POST)
    if not form.is_valid():
        return detail(request, pk, status=400, sign_form=form)
    _run(
        request,
        agreement,
        lambda: workflow.sign(agreement, signature_of(request, form), seen_sha256=form.cleaned_data["document_sha256"]),
        "Signed. The PSF will now countersign.",
    )
    return _back(request, agreement)


@login_required
@require_POST
def record_copy(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Record a signature made outside python.org by uploading the signed copy."""
    agreement = _agreement_or_404(request, pk)
    if not (agreement.is_counterparty(request.user) or is_administrator(request.user)):
        raise Http404
    form = SignedCopyForm(request.POST, request.FILES)
    if not form.is_valid():
        return detail(request, pk, status=400, copy_form=form)
    data = form.cleaned_data
    signature = workflow.Signature(
        name=data["signer_name"], title=data["signer_title"], email=data["signer_email"], signed_on=data["signed_on"]
    )
    _run(
        request,
        agreement,
        lambda: workflow.record_signed_copy(
            agreement,
            signature,
            upload=data["signed_copy"],
            user=cast("User", request.user),
            seen_sha256=data["document_sha256"],
        ),
        "Signed copy recorded. The PSF will now countersign.",
    )
    return _back(request, agreement)


@login_required
@require_POST
def withdraw(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Withdraw an unsigned offer so its draft can be changed."""
    agreement = _agreement_or_404(request, pk)
    if not (agreement.is_counterparty(request.user) or is_administrator(request.user)):
        raise Http404
    subject_url = _subject_url(request, agreement)
    if _run(
        request,
        agreement,
        lambda: workflow.withdraw(agreement, user=cast("User", request.user)),
        "Offer withdrawn.",
    ):
        return redirect(subject_url)
    return _back(request, agreement)


@administrator_required
@require_POST
def send_link(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Email a named signatory a one-time signing link."""
    agreement = _agreement_or_404(request, pk)
    form = SigningLinkForm(request.POST)
    if not form.is_valid():
        return detail(request, pk, status=400, link_form=form)
    try:
        link, token = workflow.create_signing_link(
            agreement, name=form.cleaned_data["name"], email=form.cleaned_data["email"], user=cast("User", request.user)
        )
    except workflow.InvalidTransitionError as exc:
        messages.error(request, str(exc))
    else:
        try:
            notifications.send_signing_link(request, link, token)
        except (OSError, RuntimeError):
            SigningLink.objects.filter(pk=link.pk, used_at__isnull=True).delete()
            logger.exception("Could not email signing invitation for agreement %s", agreement.pk)
            messages.error(request, "The signing link could not be emailed. Please send a new link to try again.")
        else:
            messages.success(request, f"Signing link sent to {link.email}. It expires on {link.expires_at:%B %-d, %Y}.")
    return _back(request, agreement)


def _deliver_executed_copy(request: HttpRequest, agreement: Agreement) -> bool:
    if not agreement.signer_email:
        messages.warning(
            request,
            "The agreement is executed, but no copy was emailed because the signatory has no email address. "
            "Download the signed PDF and cited terms and deliver them outside python.org.",
        )
        return False
    try:
        notifications.send_executed_copy(agreement)
    except (OSError, RuntimeError):
        logger.exception("Could not email executed agreement %s", agreement.pk)
        messages.error(
            request,
            "The agreement is executed, but its signed copy could not be emailed. "
            "Use Email signed copy to try again without countersigning.",
        )
        return False
    return True


@administrator_required
@require_POST
def countersign(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Countersign for the PSF, then email the signatory the executed copy."""
    agreement = _agreement_or_404(request, pk)
    form = CountersignForm(request.POST, request.FILES)
    if not form.is_valid():
        return detail(request, pk, status=400, countersign_form=form)
    data = form.cleaned_data
    try:
        agreement = workflow.countersign(
            agreement,
            user=cast("User", request.user),
            name=data["name"],
            title=data["title"],
            upload=data["executed_copy"],
        )
    except workflow.InvalidTransitionError as exc:
        messages.error(request, str(exc))
    else:
        if _deliver_executed_copy(request, agreement):
            messages.success(request, f"Countersigned. The signed copy was emailed to {agreement.signer_email}.")
    return _back(request, agreement)


@administrator_required
@require_POST
def resend_executed_copy(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Retry delivery without applying the PSF signature again."""
    agreement = _agreement_or_404(request, pk)
    if agreement.status != Agreement.Status.EXECUTED:
        raise Http404
    if _deliver_executed_copy(request, agreement):
        messages.success(request, f"The signed copy was emailed to {agreement.signer_email}.")
    return _back(request, agreement)


@administrator_required
@require_POST
def decline(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Decline a signed agreement."""
    agreement = _agreement_or_404(request, pk)
    form = DeclineForm(request.POST)
    if not form.is_valid():
        return detail(request, pk, status=400, decline_form=form)
    _run(
        request,
        agreement,
        lambda: workflow.decline(agreement, user=cast("User", request.user), reason=form.cleaned_data["reason"]),
        "Declined.",
    )
    return _back(request, agreement)


def _link_response(request: HttpRequest, template: str, context: dict[str, Any], status: int = 200) -> HttpResponse:
    response = render(request, template, context, status=status)
    # Keeps the token out of Referer headers to other sites. "no-referrer" would also make
    # browsers send "Origin: null" on this page's own form, which CSRF protection rejects.
    response["Referrer-Policy"] = "same-origin"
    response["Cache-Control"] = "private, no-store"
    response["X-Robots-Tag"] = "noindex"
    return response


def sign_link(request: HttpRequest, token: str) -> HttpResponse:
    """Review and sign with a one-time emailed link; no python.org account needed."""
    cast("_TrackingRequest", request).disable_tracking = True
    link = workflow.find_link(token)
    if link is None or not link.is_usable:
        return _link_response(request, "agreements/sign_link.html", {"unusable": True}, status=410)
    agreement = link.agreement
    form = SignForm(
        request.POST or None,
        initial={"document_sha256": agreement.document_sha256, "signer_name": link.name},
    )
    if request.method == "POST" and form.is_valid():
        signature = workflow.Signature(
            name=form.cleaned_data["signer_name"],
            title=form.cleaned_data["signer_title"],
            email=link.email,
            ip=get_adapter().get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
        try:
            agreement = workflow.sign_with_link(link, signature, seen_sha256=form.cleaned_data["document_sha256"])
        except workflow.DocumentChangedError as exc:
            agreement.refresh_from_db()
            form = SignForm(
                initial={
                    "document_sha256": agreement.document_sha256,
                    "signer_name": form.cleaned_data["signer_name"],
                    "signer_title": form.cleaned_data["signer_title"],
                }
            )
            messages.error(request, str(exc))
        except workflow.InvalidTransitionError:
            return _link_response(request, "agreements/sign_link.html", {"unusable": True}, status=410)
        else:
            return _link_response(
                request, "agreements/sign_link.html", {"signed": True, "agreement": agreement, "link": link}
            )
    html, metadata_hidden = documents.render_agreement_preview(documents.final_markdown(agreement))
    return _link_response(
        request,
        "agreements/sign_link.html",
        {
            "agreement": agreement,
            "link": link,
            "token": token,
            "form": form,
            "html": html,
            "metadata_hidden": metadata_hidden,
        },
        status=400 if form.errors else 200,
    )


def sign_link_document(request: HttpRequest, token: str, fmt: str) -> HttpResponse:
    """Download the document a usable signing link points to, to review or sign elsewhere."""
    cast("_TrackingRequest", request).disable_tracking = True
    link = workflow.find_link(token)
    if link is None or not link.is_usable or fmt not in documents.RENDERERS:
        raise Http404
    agreement = link.agreement
    response = file_response(
        documents.RENDERERS[fmt](documents.final_markdown(agreement)), fmt, f"agreement-{agreement.reference}"
    )
    response["Referrer-Policy"] = "same-origin"
    return response


def sign_link_terms(request: HttpRequest, token: str, version_id: int, fmt: str | None = None) -> HttpResponse:
    """Let an invited signer review only the terms cited by their unsigned agreement."""
    cast("_TrackingRequest", request).disable_tracking = True
    link = workflow.find_link(token)
    if link is None or not link.is_usable:
        raise Http404
    shown = get_object_or_404(link.agreement.terms_versions.select_related("terms"), pk=version_id)
    if fmt is not None:
        if fmt not in documents.RENDERERS:
            raise Http404
        response = file_response(
            documents.RENDERERS[fmt](documents.terms_download_markdown(shown)),
            fmt,
            f"{shown.terms.slug}-{shown.version}",
        )
        response["Referrer-Policy"] = "same-origin"
        return response
    html, toc = documents.render_html(shown.markdown)
    return _link_response(
        request,
        "agreements/terms.html",
        {"terms": shown.terms, "shown": shown, "html": html, "toc": toc, "token": token, "is_current": True},
    )
