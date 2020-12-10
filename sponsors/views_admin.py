from markupfield_helpers.helpers import render_md

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.html import mark_safe

from sponsors import use_cases
from sponsors.forms import SponsorshipReviewAdminForm
from sponsors.exceptions import SponsorshipInvalidStatusException


def preview_statement_of_work_view(ModelAdmin, request, pk):
    sow = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)
    # footnotes only work if in same markdown text as the references
    text = f"{sow.benefits_list.raw}\n\n**Legal Clauses**\n{sow.legal_clauses.raw}"
    html = render_md(text)
    ctx = {"sow": sow, "benefits_and_clauses": mark_safe(html)}
    return render(request, "sponsors/admin/preview-statement-of-work.html", context=ctx)


def reject_sponsorship_view(ModelAdmin, request, pk):
    sponsorship = get_object_or_404(ModelAdmin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        try:
            use_case = use_cases.RejectSponsorshipApplicationUseCase.build()
            use_case.execute(sponsorship)
            ModelAdmin.message_user(
                request, "Sponsorship was rejected!", messages.SUCCESS
            )
        except SponsorshipInvalidStatusException as e:
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
            except SponsorshipInvalidStatusException as e:
                ModelAdmin.message_user(request, str(e), messages.ERROR)

            redirect_url = reverse(
                "admin:sponsors_sponsorship_change", args=[sponsorship.pk]
            )
            return redirect(redirect_url)

    context = {"sponsorship": sponsorship, "form": form}
    return render(request, "sponsors/admin/approve_application.html", context=context)
