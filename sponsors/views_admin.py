from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from sponsors import use_cases
from sponsors.forms import SponsorshipReviewAdminForm, SponsorshipsListForm
from sponsors.exceptions import InvalidStatusException
from sponsors.pdf import render_contract_to_pdf_response
from sponsors.models import Sponsorship, SponsorBenefit


def preview_contract_view(ModelAdmin, request, pk):
    contract = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)
    response = render_contract_to_pdf_response(request, contract)
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


def reject_sponsorship_view(ModelAdmin, request, pk):
    sponsorship = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        try:
            use_case = use_cases.RejectSponsorshipApplicationUseCase.build()
            use_case.execute(sponsorship)
            ModelAdmin.message_user(
                request, "Sponsorship was rejected!", messages.SUCCESS
            )
        except InvalidStatusException as e:
            ModelAdmin.message_user(request, str(e), messages.ERROR)

        redirect_url = reverse(
            "admin:sponsors_sponsorship_change", args=[sponsorship.pk]
        )
        return redirect(redirect_url)

    context = {"sponsorship": sponsorship}
    return render(request, "sponsors/admin/reject_application.html", context=context)


def approve_sponsorship_view(ModelAdmin, request, pk):
    sponsorship = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)
    initial = {
        "level_name": sponsorship.level_name,
        "start_date": sponsorship.start_date,
        "end_date": sponsorship.end_date,
        "sponsorship_fee": sponsorship.sponsorship_fee,
    }

    form = SponsorshipReviewAdminForm(initial=initial, force_required=True)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        form = SponsorshipReviewAdminForm(data=request.POST)
        if form.is_valid():
            kwargs = form.cleaned_data
            kwargs["request"] = request
            try:
                use_case = use_cases.ApproveSponsorshipApplicationUseCase.build()
                use_case.execute(sponsorship, **kwargs)
                ModelAdmin.message_user(
                    request, "Sponsorship was approved!", messages.SUCCESS
                )
            except InvalidStatusException as e:
                ModelAdmin.message_user(request, str(e), messages.ERROR)

            redirect_url = reverse(
                "admin:sponsors_sponsorship_change", args=[sponsorship.pk]
            )
            return redirect(redirect_url)

    context = {"sponsorship": sponsorship, "form": form}
    return render(request, "sponsors/admin/approve_application.html", context=context)


def send_contract_view(ModelAdmin, request, pk):
    contract = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":

        use_case = use_cases.SendContractUseCase.build()
        try:
            use_case.execute(contract, request=request)
            ModelAdmin.message_user(
                request, "Contract was sent!", messages.SUCCESS
            )
        except InvalidStatusException:
            status = contract.get_status_display().title()
            ModelAdmin.message_user(
                request,
                f"Contract with status {status} can't be sent.",
                messages.ERROR,
            )

        redirect_url = reverse("admin:sponsors_contract_change", args=[contract.pk])
        return redirect(redirect_url)

    context = {"contract": contract}
    return render(request, "sponsors/admin/send_contract.html", context=context)


def rollback_to_editing_view(ModelAdmin, request, pk):
    sponsorship = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        try:
            sponsorship.rollback_to_editing()
            sponsorship.save()
            ModelAdmin.message_user(
                request, "Sponsorship is now editable!", messages.SUCCESS
            )
        except InvalidStatusException as e:
            ModelAdmin.message_user(request, str(e), messages.ERROR)

        redirect_url = reverse(
            "admin:sponsors_sponsorship_change", args=[sponsorship.pk]
        )
        return redirect(redirect_url)

    context = {"sponsorship": sponsorship}
    return render(
        request,
        "sponsors/admin/rollback_sponsorship_to_editing.html",
        context=context,
    )


def execute_contract_view(ModelAdmin, request, pk):
    contract = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":

        use_case = use_cases.ExecuteContractUseCase.build()
        try:
            use_case.execute(contract, request=request)
            ModelAdmin.message_user(
                request, "Contract was executed!", messages.SUCCESS
            )
        except InvalidStatusException:
            status = contract.get_status_display().title()
            ModelAdmin.message_user(
                request,
                f"Contract with status {status} can't be executed.",
                messages.ERROR,
            )

        redirect_url = reverse("admin:sponsors_contract_change", args=[contract.pk])
        return redirect(redirect_url)

    context = {"contract": contract}
    return render(request, "sponsors/admin/execute_contract.html", context=context)


def nullify_contract_view(ModelAdmin, request, pk):
    contract = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":

        use_case = use_cases.NullifyContractUseCase.build()
        try:
            use_case.execute(contract, request=request)
            ModelAdmin.message_user(
                request, "Contract was nullified!", messages.SUCCESS
            )
        except InvalidStatusException:
            status = contract.get_status_display().title()
            ModelAdmin.message_user(
                request,
                f"Contract with status {status} can't be nullified.",
                messages.ERROR,
            )

        redirect_url = reverse("admin:sponsors_contract_change", args=[contract.pk])
        return redirect(redirect_url)

    context = {"contract": contract}
    return render(request, "sponsors/admin/nullify_contract.html", context=context)

@transaction.atomic
def update_related_sponsorships(ModelAdmin, request, pk):
    """
    Given a SponsorshipBeneefit, update all releated SponsorBenefit from
    the Sponsorship listed in the post payload
    """
    benefit = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)
    initial = {"sponsorships": [sp.pk for sp in benefit.related_sponsorships]}
    form = SponsorshipsListForm.with_benefit(benefit, initial=initial)

    if request.method == "POST":
        form = SponsorshipsListForm.with_benefit(benefit, data=request.POST)
        if form.is_valid():
            sponsorships = form.cleaned_data["sponsorships"]

            related_benefits = benefit.sponsorbenefit_set.all()
            for sp in sponsorships:
                sponsor_benefit = related_benefits.get(sponsorship=sp)
                sponsor_benefit.delete()

                # recreate sponsor benefit considering updated benefit/feature configs
                SponsorBenefit.new_copy(
                    benefit,
                    sponsorship=sp,
                    added_by_user=sponsor_benefit.added_by_user
                )

            ModelAdmin.message_user(
                request, f"{len(sponsorships)} related sponsorships updated!", messages.SUCCESS
            )
            redirect_url = reverse(
                "admin:sponsors_sponsorshipbenefit_change", args=[benefit.pk]
            )
            return redirect(redirect_url)

    context = {"benefit": benefit, "form": form}
    return render(request, "sponsors/admin/update_related_sponsorships.html", context=context)
