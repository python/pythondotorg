"""Custom contract drafting and offers."""

from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.agreements import documents, workflow
from apps.agreements.auth import administrator_required, is_administrator, preparer_required
from apps.agreements.forms.contracts import CustomContractForm
from apps.agreements.kinds import CustomContractKind
from apps.agreements.models import CustomContract


def _custom_or_404(pk, *, for_update=False):
    contracts = CustomContract.objects.select_related("agreement", "terms")
    if for_update:
        contracts = contracts.select_for_update(of=("self",))
    return get_object_or_404(contracts, pk=pk)


@preparer_required
def custom_create(request):
    """Write a new one-off contract."""
    form = CustomContractForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.instance.created_by = request.user
        contract = form.save()
        return redirect(contract)
    return render(request, "agreements/custom_form.html", {"form": form, "nav": "custom"})


@preparer_required
@transaction.atomic
def custom_edit(request, pk):
    """Change a contract that hasn't been offered; once offered, edit the agreement instead."""
    contract = _custom_or_404(pk, for_update=request.method == "POST")
    if contract.agreement_id is not None:
        if not is_administrator(request.user):
            return redirect(contract.agreement)
        return redirect("agreements:edit", pk=contract.agreement_id)
    form = CustomContractForm(request.POST or None, instance=contract)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect(contract)
    return render(request, "agreements/custom_form.html", {"form": form, "contract": contract, "nav": "custom"})


@preparer_required
def custom_detail(request, pk):
    """Preview a draft contract; once offered, the agreement page takes over."""
    contract = _custom_or_404(pk)
    if contract.agreement:
        return redirect(contract.agreement)
    kind = CustomContractKind()
    html, _ = documents.render_html(documents.preview_markdown(kind.compose(contract), contract.counterparty_name))
    return render(request, "agreements/custom_detail.html", {"contract": contract, "html": html, "nav": "custom"})


@administrator_required
@require_POST
def custom_offer(request, pk):
    """Freeze the draft and make it ready to sign."""
    contract = _custom_or_404(pk)
    try:
        agreement = workflow.offer(CustomContractKind(), contract, user=request.user)
    except (workflow.InvalidTransitionError, ValueError) as exc:
        messages.error(request, str(exc))
        return redirect(contract)
    messages.success(request, "Ready to sign. Send a signing link, or record a signed copy when it comes back.")
    return redirect(agreement)


@preparer_required
@require_POST
@transaction.atomic
def custom_delete(request, pk):
    """Discard a draft that was never offered."""
    contract = _custom_or_404(pk, for_update=True)
    if contract.agreement_id is not None:
        raise Http404
    contract.delete()
    messages.success(request, "Draft discarded.")
    return redirect("agreements:queue")
