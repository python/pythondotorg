"""Program browsing, order selection, and shared agreement signing entry points."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from apps.agreements import documents as agreement_documents
from apps.agreements import workflow
from apps.agreements.auth import can_prepare, is_administrator, preparer_required
from apps.agreements.documents import sha256
from apps.agreements.forms.signing import SignForm
from apps.agreements.models import Order, OrderLine, Program
from apps.agreements.orders import documents
from apps.agreements.orders.forms import OrderBuilder
from apps.agreements.orders.pricing import build_quote, money
from apps.agreements.registry import get_kind
from apps.agreements.views.helpers import action_forms, file_response, signature_of

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.contrib.auth.models import AnonymousUser
    from django.db.models import QuerySet
    from django.http import HttpRequest, HttpResponse

    from apps.users.models import User

KIND = "order"


def _orders() -> QuerySet[Order]:
    return Order.objects.select_related("program", "created_by", "customer_account", "agreement").prefetch_related(
        Prefetch("agreements", queryset=OrderLine.objects.all())
    )


def _own_orders(user: User | AnonymousUser) -> QuerySet[Order]:
    if not user.is_authenticated:
        return _orders().none()
    owned = Q(customer_account=user)
    if can_prepare(user):
        owned |= Q(created_by=user)
    return _orders().filter(owned)


def _order_rows(orders: Iterable[Order]) -> list[dict[str, Any]]:
    """Keep stale drafts reachable without presenting an invented price."""
    rows: list[dict[str, Any]] = []
    for order in orders:
        row: dict[str, Any] = {"order": order}
        try:
            row["selections"] = [(line.agreement_obj.short_name, line.tier_name) for line in order.agreement_list]
            row["fees"] = order.fee_totals
        except (ValidationError, KeyError):
            if not order.is_editable:
                raise
            row["review_selections"] = True
        rows.append(row)
    return rows


def _order_or_404(request: HttpRequest, pk: UUID, *, for_update: bool = False) -> Order:
    orders = _orders() if can_prepare(request.user) else _own_orders(request.user)
    if for_update:
        orders = orders.select_for_update(of=("self",))
    return get_object_or_404(orders, pk=pk)


def _program_or_404(request: HttpRequest, slug: str) -> Program:
    return get_object_or_404(Program.visible_to(request.user), slug=slug)


@never_cache
@require_GET
def program_list(request: HttpRequest) -> HttpResponse:
    """List only programs the visitor may browse."""
    return render(
        request,
        "agreements/orders/program_list.html",
        {
            "programs": Program.visible_to(request.user),
            "nav": "programs",
        },
    )


@never_cache
@require_GET
def program_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Compare a program's configured agreements and the visitor's recent orders."""
    program = _program_or_404(request, slug)
    agreements = list(program.catalog.agreements.values())
    return render(
        request,
        "agreements/orders/overview.html",
        {
            "program": program,
            "catalog": program.catalog,
            "agreements": agreements,
            "under_review": any(agreement.terms.under_review for agreement in agreements),
            "orders": _order_rows(_own_orders(request.user).filter(program=program)[:5]),
            "nav": "programs",
        },
    )


@never_cache
@require_GET
def quote(request: HttpRequest, slug: str) -> JsonResponse:
    """Price valid selections without exposing a private program to unrelated visitors."""
    order = None
    if request.GET.get("order"):
        try:
            pk = UUID(request.GET["order"])
        except ValueError:
            raise Http404 from None
        order = _order_or_404(request, pk)
        if order.program.slug != slug or not order.can_edit(request.user):
            raise Http404
        program = order.program
    else:
        program = _program_or_404(request, slug)
    builder = OrderBuilder(
        request.GET,
        program=program,
        order=order,
        staff=can_prepare(request.user),
        can_link_accounts=is_administrator(request.user),
    )
    selections = builder.order_form.fields["agreements"]
    errors: dict[str, dict[str, list[dict[str, str]]] | list[str]] = {}
    try:
        # No selection is a useful empty quote, not a submitted order.
        chosen = selections.clean(request.GET.getlist("agreements")) if request.GET.getlist("agreements") else []
        discount = builder.order_form.fields["discount"].clean(request.GET.get("discount"))
    except ValidationError as exc:
        return JsonResponse({"errors": {"selections": exc.messages}}, status=400)
    quotes: list[dict[str, Any]] = []
    for key in builder.agreements:
        if key not in chosen:
            continue
        form = builder.agreement_forms[key]
        if not form.is_valid():
            errors[key] = form.errors.get_json_data()
            continue
        try:
            priced = build_quote(
                builder.agreements[key], form.cleaned_data["tier"], discount, form.cleaned_data["addons"]
            )
        except ValidationError as exc:
            errors[key] = exc.messages
            continue
        quotes.append(
            {
                "slug": key,
                "name": builder.agreements[key].short_name,
                "services": form.cleaned_data["services"],
                **priced.as_dict(),
            }
        )
    if errors:
        return JsonResponse({"errors": errors}, status=400)
    total_annual = sum((Decimal(q["total_annual"]) for q in quotes), Decimal(0))
    term_total = sum((Decimal(q["term_total"]) for q in quotes), Decimal(0))
    return JsonResponse(
        {
            "agreements": quotes,
            "term_months": builder.catalog.discount(discount).term_months,
            "display": {"total_annual": money(total_annual), "term_total": money(term_total)},
        }
    )


def _builder(request: HttpRequest, program: Program, order: Order | None = None) -> HttpResponse:
    staff = can_prepare(request.user)
    builder = OrderBuilder(
        request.POST or None,
        program=program,
        order=order,
        staff=staff,
        can_link_accounts=is_administrator(request.user),
    )
    if not order:
        preselect = [slug for slug in request.GET.getlist("agreement") if slug in builder.agreements]
        builder.order_form.initial["agreements"] = preselect
    if request.method == "POST" and builder.is_valid():
        return redirect(builder.save(cast("User", request.user)))
    return render(
        request,
        "agreements/orders/order_form.html",
        {
            "builder": builder,
            "form": builder.order_form,
            "program": program,
            "catalog": builder.catalog,
            "agreements": list(builder.agreements.values()),
            "order": order,
            "staff": staff,
            "nav": "orders",
            "can_browse_program": program.is_public or staff,
        },
    )


@never_cache
def order_create(request: HttpRequest, slug: str) -> HttpResponse:
    """Start a public order, or a staff-prepared private order."""
    program = _program_or_404(request, slug)
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    return _builder(request, program)


@never_cache
@login_required
@transaction.atomic
def order_edit(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Change selections until the Order Form is offered for signature."""
    order = _order_or_404(request, pk, for_update=request.method == "POST")
    if not order.can_edit(request.user):
        messages.error(request, "This Order Form is out for signature. Withdraw it to change the selections.")
        return redirect(order)
    return _builder(request, order.program, order)


@never_cache
@login_required
def order_list(request: HttpRequest) -> HttpResponse:
    """List the customer's orders, including drafts needing revised selections."""
    return render(
        request,
        "agreements/orders/order_list.html",
        {
            "orders": _order_rows(_own_orders(request.user)),
            "nav": "orders",
        },
    )


@never_cache
@login_required
def order_detail(request: HttpRequest, pk: UUID, sign_form: SignForm | None = None, status: int = 200) -> HttpResponse:
    """Review the order and use the common account, link, or signed-copy actions."""
    order = _order_or_404(request, pk)
    user = request.user
    context: dict[str, Any] = {
        "order": order,
        "is_customer": order.is_customer(user),
        "can_prepare": can_prepare(user),
        "is_administrator": is_administrator(user),
        "can_offer": order.can_offer(user),
        "can_edit": order.can_edit(user),
        "nav": "staff" if can_prepare(user) and not order.is_customer(user) else "orders",
        "next": order.get_absolute_url(),
    }
    try:
        markdown = documents.order_form_markdown(order)
    except (ValidationError, KeyError):
        if not order.is_editable:
            raise
        context["configuration_error"] = "The available selections have changed. Edit this draft before signing."
    else:
        context["html"], context["metadata_hidden"] = agreement_documents.render_agreement_preview(markdown)
        context["lines"] = order.agreement_list
        if order.agreement:
            context.update(action_forms(request, order.agreement))
        elif order.is_customer(user):
            context["draft_sign_form"] = sign_form or SignForm(
                initial={
                    "document_sha256": sha256(documents.compose_order_form_markdown(order)),
                    "signer_name": cast("User", user).get_full_name(),
                }
            )
    return render(request, "agreements/orders/order_detail.html", context, status=status)


@never_cache
@login_required
@require_POST
@transaction.atomic
def order_sign(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Freeze and sign the reviewed draft in one atomic transition."""
    order = _order_or_404(request, pk, for_update=True)
    if not order.is_customer(request.user) or not order.is_editable:
        raise Http404
    form = SignForm(request.POST)
    if not form.is_valid():
        return order_detail(request, pk, sign_form=form, status=400)
    try:
        with transaction.atomic():
            agreement = workflow.offer(get_kind(KIND), order, user=cast("User", request.user))
            workflow.sign(agreement, signature_of(request, form), seen_sha256=form.cleaned_data["document_sha256"])
    except (workflow.InvalidTransitionError, ValidationError) as exc:
        messages.error(request, "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))
    else:
        messages.success(request, "Signed. The PSF will now countersign the Order Form.")
    return redirect(order)


@never_cache
@login_required
@require_POST
@transaction.atomic
def order_offer(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Fix the text for an account, a signing link, or an externally signed copy."""
    order = _order_or_404(request, pk, for_update=True)
    if not order.can_offer(request.user):
        raise Http404
    try:
        workflow.offer(get_kind(KIND), order, user=cast("User", request.user))
    except (workflow.InvalidTransitionError, ValidationError) as exc:
        messages.error(request, "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc))
    else:
        messages.success(request, "The Order Form is ready to sign. Its text is fixed until it is signed or withdrawn.")
    return redirect(order)


@login_required
@require_POST
@transaction.atomic
def order_delete(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Discard an authorized draft without touching offered agreements."""
    order = _order_or_404(request, pk, for_update=True)
    if not order.can_edit(request.user):
        raise Http404
    order.delete()
    messages.success(request, "Draft discarded.")
    return redirect("agreements:order_list")


@login_required
def order_document(request: HttpRequest, pk: UUID, fmt: str) -> HttpResponse:
    """Download the authorized order's draft or frozen document."""
    order = _order_or_404(request, pk)
    if fmt not in agreement_documents.RENDERERS:
        raise Http404
    try:
        markdown = documents.order_form_markdown(order)
    except (ValidationError, KeyError):
        if not order.is_editable:
            raise
        messages.error(request, "The available selections have changed. Edit this draft before downloading it.")
        return redirect(order)
    return file_response(
        agreement_documents.RENDERERS[fmt](markdown), fmt, f"order-form-{order.reference}-{order.status}"
    )


@never_cache
@preparer_required
def staff_orders(request: HttpRequest) -> HttpResponse:
    """List all orders for agreement managers."""
    return render(request, "agreements/orders/staff_queue.html", {"orders": _order_rows(_orders()), "nav": "staff"})
