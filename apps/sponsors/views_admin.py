"""Admin action views for managing sponsorships and contracts."""

import io
import zipfile
from tempfile import NamedTemporaryFile

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.sponsors import use_cases
from apps.sponsors.contracts import render_contract_to_docx_response, render_contract_to_pdf_response
from apps.sponsors.exceptions import InvalidStatusError
from apps.sponsors.forms import (
    CloneApplicationConfigForm,
    SendSponsorshipNotificationForm,
    SignedSponsorshipReviewAdminForm,
    SponsorshipReviewAdminForm,
    SponsorshipsListForm,
)
from apps.sponsors.models import BenefitFeature, EmailTargetable, SponsorshipCurrentYear


def preview_contract_view(model_admin, request, pk):
    """Render a contract preview as PDF or DOCX based on the format query parameter."""
    contract = get_object_or_404(model_admin.get_queryset(request), pk=pk)
    output_format = request.GET.get("format", "pdf")
    if output_format == "docx":
        response = render_contract_to_docx_response(request, contract)
    else:
        response = render_contract_to_pdf_response(request, contract)
    response["X-Frame-Options"] = "SAMEORIGIN"
    return response


def reject_sponsorship_view(model_admin, request, pk):
    """Handle rejection of a sponsorship application with confirmation."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        try:
            use_case = use_cases.RejectSponsorshipApplicationUseCase.build()
            use_case.execute(sponsorship)
            model_admin.message_user(request, "Sponsorship was rejected!", messages.SUCCESS)
        except InvalidStatusError as e:
            model_admin.message_user(request, str(e), messages.ERROR)

        redirect_url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk])
        return redirect(redirect_url)

    context = {"sponsorship": sponsorship}
    return render(request, "sponsors/admin/reject_application.html", context=context)


def approve_sponsorship_view(model_admin, request, pk):
    """Approves a sponsorship and create an empty contract."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)
    initial = {
        "package": sponsorship.package,
        "start_date": sponsorship.start_date,
        "end_date": sponsorship.end_date,
        "sponsorship_fee": sponsorship.sponsorship_fee,
    }

    form = SponsorshipReviewAdminForm(initial=initial, force_required=True)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        form = SponsorshipReviewAdminForm(data=request.POST, force_required=True)
        if form.is_valid():
            kwargs = form.cleaned_data
            kwargs["request"] = request
            try:
                use_case = use_cases.ApproveSponsorshipApplicationUseCase.build()
                use_case.execute(sponsorship, **kwargs)
                model_admin.message_user(request, "Sponsorship was approved!", messages.SUCCESS)
            except InvalidStatusError as e:
                model_admin.message_user(request, str(e), messages.ERROR)

            redirect_url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk])
            return redirect(redirect_url)

    context = {
        "sponsorship": sponsorship,
        "form": form,
        "previous_effective": sponsorship.previous_effective_date or "UNKNOWN",
    }
    return render(request, "sponsors/admin/approve_application.html", context=context)


def approve_signed_sponsorship_view(model_admin, request, pk):
    """Approves a sponsorship and execute contract for existing file."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)
    initial = {
        "package": sponsorship.package,
        "start_date": sponsorship.start_date,
        "end_date": sponsorship.end_date,
        "sponsorship_fee": sponsorship.sponsorship_fee,
    }

    form = SignedSponsorshipReviewAdminForm(initial=initial, force_required=True)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        form = SignedSponsorshipReviewAdminForm(request.POST, request.FILES, force_required=True)
        if form.is_valid():
            kwargs = form.cleaned_data
            kwargs["request"] = request
            try:
                # create the sponsorship + contract
                use_case = use_cases.ApproveSponsorshipApplicationUseCase.build()
                sponsorship = use_case.execute(sponsorship, **kwargs)
                # execute it using existing contract
                use_case = use_cases.ExecuteExistingContractUseCase.build()
                use_case.execute(sponsorship.contract, kwargs["signed_contract"], request=request)
                model_admin.message_user(request, "Signed sponsorship was approved!", messages.SUCCESS)
            except InvalidStatusError as e:
                model_admin.message_user(request, str(e), messages.ERROR)

            redirect_url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk])
            return redirect(redirect_url)

    context = {"sponsorship": sponsorship, "form": form}
    return render(request, "sponsors/admin/approve_application.html", context=context)


def send_contract_view(model_admin, request, pk):
    """Send a finalized contract to the sponsor for signature."""
    contract = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        use_case = use_cases.SendContractUseCase.build()
        try:
            use_case.execute(contract, request=request)
            model_admin.message_user(request, "Contract was sent!", messages.SUCCESS)
        except InvalidStatusError:
            status = contract.get_status_display().title()
            model_admin.message_user(
                request,
                f"Contract with status {status} can't be sent.",
                messages.ERROR,
            )

        redirect_url = reverse("admin:sponsors_contract_change", args=[contract.pk])
        return redirect(redirect_url)

    context = {"contract": contract}
    return render(request, "sponsors/admin/send_contract.html", context=context)


def rollback_to_editing_view(model_admin, request, pk):
    """Roll back a sponsorship to editing status with confirmation."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        try:
            sponsorship.rollback_to_editing()
            sponsorship.save()
            model_admin.message_user(request, "Sponsorship is now editable!", messages.SUCCESS)
        except InvalidStatusError as e:
            model_admin.message_user(request, str(e), messages.ERROR)

        redirect_url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk])
        return redirect(redirect_url)

    context = {"sponsorship": sponsorship}
    return render(
        request,
        "sponsors/admin/rollback_sponsorship_to_editing.html",
        context=context,
    )


def unlock_view(model_admin, request, pk):
    """Unlock a sponsorship to allow editing with confirmation."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        try:
            sponsorship.locked = False
            sponsorship.save(update_fields=["locked"])
            model_admin.message_user(request, "Sponsorship is now unlocked!", messages.SUCCESS)
        except InvalidStatusError as e:
            model_admin.message_user(request, str(e), messages.ERROR)

        redirect_url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk])
        return redirect(redirect_url)

    context = {"sponsorship": sponsorship}
    return render(
        request,
        "sponsors/admin/unlock.html",
        context=context,
    )


def lock_view(model_admin, request, pk):
    """Lock a sponsorship to prevent further editing."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    sponsorship.locked = True
    sponsorship.save()

    redirect_url = reverse("admin:sponsors_sponsorship_change", args=[sponsorship.pk])
    return redirect(redirect_url)


def execute_contract_view(model_admin, request, pk):
    """Execute a contract by uploading the signed document."""
    contract = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    is_post = request.method.upper() == "POST"
    signed_document = request.FILES.get("signed_document")
    if is_post and request.POST.get("confirm") == "yes" and signed_document:
        use_case = use_cases.ExecuteContractUseCase.build()
        try:
            use_case.execute(contract, signed_document, request=request)
            model_admin.message_user(request, "Contract was executed!", messages.SUCCESS)
        except InvalidStatusError:
            status = contract.get_status_display().title()
            model_admin.message_user(
                request,
                f"Contract with status {status} can't be executed.",
                messages.ERROR,
            )

        redirect_url = reverse("admin:sponsors_contract_change", args=[contract.pk])
        return redirect(redirect_url)

    error_msg = ""
    if is_post and not signed_document:
        error_msg = "You must submit the signed contract document to execute it."

    context = {"contract": contract, "error_msg": error_msg}
    return render(request, "sponsors/admin/execute_contract.html", context=context)


def nullify_contract_view(model_admin, request, pk):
    """Nullify a contract with confirmation."""
    contract = get_object_or_404(model_admin.get_queryset(request), pk=pk)

    if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
        use_case = use_cases.NullifyContractUseCase.build()
        try:
            use_case.execute(contract, request=request)
            model_admin.message_user(request, "Contract was nullified!", messages.SUCCESS)
        except InvalidStatusError:
            status = contract.get_status_display().title()
            model_admin.message_user(
                request,
                f"Contract with status {status} can't be nullified.",
                messages.ERROR,
            )

        redirect_url = reverse("admin:sponsors_contract_change", args=[contract.pk])
        return redirect(redirect_url)

    context = {"contract": contract}
    return render(request, "sponsors/admin/nullify_contract.html", context=context)


@transaction.atomic
def update_related_sponsorships(model_admin, request, pk):
    """Update all related SponsorBenefit from a SponsorshipBenefit.

    Use the Sponsorship listed in the post payload to determine
    which SponsorBenefits to update.
    """
    qs = model_admin.get_queryset(request).select_related("program")
    benefit = get_object_or_404(qs, pk=pk)
    initial = {"sponsorships": [sp.pk for sp in benefit.related_sponsorships]}
    form = SponsorshipsListForm.with_benefit(benefit, initial=initial)

    if request.method == "POST":
        form = SponsorshipsListForm.with_benefit(benefit, data=request.POST)
        if form.is_valid():
            sponsorships = form.cleaned_data["sponsorships"]

            related_benefits = benefit.sponsorbenefit_set.all()
            for sp in sponsorships:
                sponsor_benefit = related_benefits.get(sponsorship=sp)
                sponsor_benefit.reset_attributes(benefit)

            model_admin.message_user(request, f"{len(sponsorships)} related sponsorships updated!", messages.SUCCESS)
            redirect_url = reverse("admin:sponsors_sponsorshipbenefit_change", args=[benefit.pk])
            return redirect(redirect_url)

    context = {"benefit": benefit, "form": form}
    return render(request, "sponsors/admin/update_related_sponsorships.html", context=context)


def list_uploaded_assets(model_admin, request, pk):
    """List and export assets uploaded by the user."""
    sponsorship = get_object_or_404(model_admin.get_queryset(request), pk=pk)
    assets = BenefitFeature.objects.required_assets().from_sponsorship(sponsorship)
    context = {"sponsorship": sponsorship, "assets": assets}
    return render(request, "sponsors/admin/list_uploaded_assets.html", context=context)


def clone_application_config(model_admin, request):
    """Clone sponsorship application configuration from one year to another."""
    form = CloneApplicationConfigForm()
    context = {
        "current_year": SponsorshipCurrentYear.get_year(),
        "configured_years": form.configured_years,
        "new_year": None,
    }
    if request.method == "POST":
        form = CloneApplicationConfigForm(data=request.POST)
        if form.is_valid():
            use_case = use_cases.CloneSponsorshipYearUseCase.build()
            target_year = form.cleaned_data["target_year"]
            from_year = form.cleaned_data["from_year"]
            use_case.execute(from_year, target_year, request=request)

            context["configured_years"].insert(0, target_year)
            context["new_year"] = target_year
            model_admin.message_user(
                request,
                f"Benefits and Packages for {target_year} copied with sucess from {from_year}!",
                messages.SUCCESS,
            )

    context["form"] = form
    template = "sponsors/admin/clone_application_config_form.html"
    return render(request, template, context)


##################
### CUSTOM ACTIONS
def send_sponsorship_notifications_action(model_admin, request, queryset):
    """Send email notifications to selected sponsorships with preview support."""
    to_notify = queryset.includes_benefit_feature(EmailTargetable)
    to_ignore = queryset.exclude(id__in=to_notify.values_list("id", flat=True))
    email_preview = None

    post_request = request.method.upper() == "POST"
    if post_request and "confirm" in request.POST:
        form = SendSponsorshipNotificationForm(request.POST)
        if form.is_valid():
            use_case = use_cases.SendSponsorshipNotificationUseCase.build()
            kwargs = {
                "sponsorships": queryset,
                "notification": form.get_notification(),
                "contact_types": form.cleaned_data["contact_types"],
                "request": request,
            }
            use_case.execute(**kwargs)
            model_admin.message_user(request, "Notifications were sent!", messages.SUCCESS)

            redirect_url = reverse("admin:sponsors_sponsorship_changelist")
            return redirect(redirect_url)
    elif post_request and "preview" in request.POST:
        form = SendSponsorshipNotificationForm(request.POST)
        if form.is_valid():
            msg_kwargs = {
                "to_primary": True,
                "to_administrative": True,
                "to_accounting": True,
                "to_manager": True,
            }
            notification = form.get_notification()
            email_preview = notification.get_email_message(queryset.first(), **msg_kwargs)
    else:
        form = SendSponsorshipNotificationForm()

    context = {
        "to_notify": to_notify,
        "to_ignore": to_ignore,
        "form": form,
        "email_preview": email_preview,
        "queryset": queryset,
    }
    return render(request, "sponsors/admin/send_sponsors_notification.html", context=context)


def export_assets_as_zipfile(model_admin, request, queryset):
    """Export a zip file with data associated with the assets.

    The sponsor names are used as directories to group assets from a same sponsor.
    """
    if not queryset.exists():
        model_admin.message_user(request, "You have to select at least one asset to export.", messages.WARNING)
        return redirect(request.path)

    assets_without_values = [asset for asset in queryset if not asset.has_value]
    if any(assets_without_values):
        model_admin.message_user(
            request,
            f"{len(assets_without_values)} assets from the selection doesn't have data to export. Please review your selection!",
            messages.WARNING,
        )
        return redirect(request.path)

    buffer = io.BytesIO()
    zip_file = zipfile.ZipFile(buffer, "w")

    for asset in queryset:
        zipdir = "unknown"  # safety belt
        if asset.from_sponsorship:
            zipdir = asset.content_object.sponsor.name
        elif asset.from_sponsor:
            zipdir = asset.content_object.name

        if not asset.is_file:
            zip_file.writestr(f"{zipdir}/{asset.internal_name}.txt", asset.value)
        else:
            suffix = "." + asset.value.name.split(".")[-1]
            prefix = asset.internal_name
            with NamedTemporaryFile(suffix=suffix, prefix=prefix) as temp_file:
                temp_file.write(asset.value.read())
                zip_file.write(temp_file.name, arcname=f"{zipdir}/{prefix}{suffix}")

    zip_file.close()
    response = HttpResponse(buffer.getvalue())
    response["Content-Type"] = "application/x-zip-compressed"
    response["Content-Disposition"] = "attachment; filename=assets.zip"

    return response
