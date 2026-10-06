"""Published terms and staff editing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache

from apps.agreements import documents, workflow
from apps.agreements.auth import can_prepare, is_administrator, preparer_required
from apps.agreements.forms.terms import TermsForm
from apps.agreements.models import Terms
from apps.agreements.views.helpers import _diff, file_response

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser
    from django.http import HttpRequest, HttpResponse

    from apps.agreements.models import TermsVersion
    from apps.users.models import User


def _version_or_404(terms: Terms, version: str | None) -> TermsVersion:
    if version is None:
        current = terms.current_version
        if current is None:
            raise Http404
        return current
    return get_object_or_404(terms.versions, version=version)


def _can_read_terms(user: User | AnonymousUser, shown: TermsVersion) -> bool:
    if shown.terms.is_public or can_prepare(user):
        return True
    if not user.is_authenticated:
        return False
    if shown.agreements.filter(counterparty_account=user).exists():
        return True
    # Customers reviewing a staff-prepared draft need its current terms before it is offered.
    from apps.agreements.models import OrderLine

    lines = OrderLine.objects.filter(
        order__customer_account=user,
        order__agreement__isnull=True,
    ).select_related("order__program")
    return any(
        line.agreement in line.order.catalog.agreements
        and line.agreement_obj.terms_slug == shown.terms.slug
        and shown.pk == cast("TermsVersion", shown.terms.current_version).pk
        for line in lines
    )


def _readable_terms(request: HttpRequest, slug: str, version: str | None) -> tuple[Terms, TermsVersion]:
    terms = get_object_or_404(Terms, slug=slug)
    shown = _version_or_404(terms, version)
    if not _can_read_terms(request.user, shown):
        raise Http404
    return terms, shown


def _terms_cache(request: HttpRequest, response: HttpResponse, terms: Terms) -> HttpResponse:
    public = terms.is_public and not request.user.is_authenticated
    response["Cache-Control"] = "public, max-age=3600" if public else "private, no-store"
    if not terms.is_public:
        response["X-Robots-Tag"] = "noindex"
    return response


def terms(request: HttpRequest, slug: str, version: str | None = None) -> HttpResponse:
    """Read one published version of terms; without a version, the current one."""
    terms, shown = _readable_terms(request, slug, version)
    html, toc = documents.render_html(shown.markdown)
    response = render(
        request,
        "agreements/terms.html",
        {
            "terms": terms,
            "shown": shown,
            "is_current": shown == terms.current_version,
            "html": html,
            "toc": toc,
            "can_edit": can_prepare(request.user),
            "can_read_current": terms.is_public or can_prepare(request.user),
        },
    )
    return _terms_cache(request, response, terms)


def terms_download(request: HttpRequest, slug: str, fmt: str, version: str | None = None) -> HttpResponse:
    """Download one published version of terms as PDF or DOCX."""
    terms, shown = _readable_terms(request, slug, version)
    if fmt not in documents.RENDERERS:
        raise Http404
    content = documents.RENDERERS[fmt](documents.terms_download_markdown(shown))
    response = file_response(content, fmt, f"{terms.slug}-{shown.version}")
    return _terms_cache(request, response, terms)


@never_cache
@preparer_required
def terms_list(request: HttpRequest) -> HttpResponse:
    """Every set of terms, for staff to edit."""
    return render(
        request, "agreements/terms_list.html", {"all_terms": Terms.objects.prefetch_related("versions"), "nav": "terms"}
    )


@never_cache
@preparer_required
def terms_edit(request: HttpRequest, slug: str) -> HttpResponse:
    """Prepare draft text; only administrators configure or publish terms."""
    terms = get_object_or_404(Terms, slug=slug)
    current = terms.current_version
    administrator = is_administrator(request.user)
    if (
        request.method == "POST"
        and not administrator
        and (
            request.POST.get("action") == TermsForm.PUBLISH
            or any(field in request.POST for field in ("under_review", "is_public", "version", "notes"))
        )
    ):
        raise PermissionDenied
    initial: dict[str, Any] = {
        "markdown": terms.draft_markdown or (current.markdown if current else ""),
        "under_review": terms.under_review,
        "is_public": terms.is_public,
    }
    form = TermsForm(request.POST or None, initial=initial, terms=terms, can_publish=administrator)
    preview = diff = None
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if "preview" in request.POST:
            preview, _ = documents.render_html(data["markdown"])
        elif data["action"] == TermsForm.PUBLISH:
            terms.under_review = data["under_review"]
            terms.is_public = data["is_public"]
            terms.save(update_fields=["under_review", "is_public"])
            published = workflow.publish_terms(
                terms,
                version=data["version"],
                markdown=data["markdown"],
                notes=data["notes"],
                user=cast("User", request.user),
            )
            messages.success(request, f"Published version {published.version}. New documents cite it from now on.")
            return redirect(published)
        else:
            if administrator:
                terms.under_review = data["under_review"]
                terms.is_public = data["is_public"]
                terms.save(update_fields=["under_review", "is_public"])
            workflow.save_terms_draft(terms, markdown=data["markdown"], user=cast("User", request.user))
            messages.success(request, "Draft saved. Draft text stays private.")
            return redirect("agreements:terms_edit", slug=terms.slug)
    working = (
        form.data.get("markdown", initial["markdown"]).replace("\r\n", "\n") if form.is_bound else initial["markdown"]
    )
    if current:
        diff = _diff(current.markdown, working)
    return render(
        request,
        "agreements/terms_edit.html",
        {
            "terms": terms,
            "current": current,
            "versions": terms.versions.select_related("published_by"),
            "form": form,
            "preview": preview,
            "diff": diff,
            "nav": "terms",
        },
        status=400 if form.errors else 200,
    )
