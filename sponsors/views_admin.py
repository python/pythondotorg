from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse

from sponsors import use_cases
from sponsors.forms import SponsorshipReviewAdminForm
from sponsors.exceptions import InvalidStatusException
from sponsors.pdf import render_contract_to_pdf_response


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
            ModelAdmin.message_user(request, "Contract was sent!", messages.SUCCESS)
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
