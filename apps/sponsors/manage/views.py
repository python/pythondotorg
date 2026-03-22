"""Views for the sponsor management UI.

Locked down to users in the 'Sponsorship Admin' group (or staff/superuser).
"""

import contextlib
import csv
import io
import zipfile
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from apps.sponsors import use_cases
from apps.sponsors.exceptions import InvalidStatusError
from apps.sponsors.manage.forms import (
    CONFIG_TYPES,
    AddBenefitToSponsorshipForm,
    BenefitFilterForm,
    CloneYearForm,
    ComposerSponsorForm,
    ComposerTermsForm,
    CurrentYearForm,
    ExecuteContractForm,
    NotificationTemplateForm,
    SendSponsorshipNotificationManageForm,
    SponsorContactForm,
    SponsorEditForm,
    SponsorshipApproveForm,
    SponsorshipApproveSignedForm,
    SponsorshipBenefitManageForm,
    SponsorshipEditForm,
    SponsorshipFilterForm,
    SponsorshipPackageManageForm,
)
from apps.sponsors.models import (
    BenefitFeature,
    BenefitFeatureConfiguration,
    Contract,
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    SponsorEmailNotificationTemplate,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)
from pydotorg.mixins import GroupRequiredMixin, LoginRequiredMixin


class SponsorshipAdminRequiredMixin(LoginRequiredMixin, GroupRequiredMixin):
    """Require user to be in 'Sponsorship Admin' group or be staff."""

    group_required = "Sponsorship Admin"
    raise_exception = True

    def check_membership(self, group):
        """Allow staff users in addition to group members."""
        if self.request.user.is_staff:
            return True
        return super().check_membership(group)


class ManageDashboardView(SponsorshipAdminRequiredMixin, TemplateView):
    """Dashboard showing sponsorship configuration overview by year."""

    template_name = "sponsors/manage/dashboard.html"

    def get_context_data(self, **kwargs):
        """Return dashboard context with year stats and program breakdowns."""
        context = super().get_context_data(**kwargs)

        # Get all years with benefits
        years = SponsorshipBenefit.objects.values_list("year", flat=True).distinct().order_by("-year")
        years = [y for y in years if y]

        current_year = None
        with contextlib.suppress(SponsorshipCurrentYear.DoesNotExist):
            current_year = SponsorshipCurrentYear.get_year()

        selected_year = self.request.GET.get("year")
        if selected_year:
            selected_year = int(selected_year)
        elif current_year:
            selected_year = current_year
        elif years:
            selected_year = years[0]

        # Stats for the selected year
        year_benefits = (
            SponsorshipBenefit.objects.filter(year=selected_year)
            if selected_year
            else SponsorshipBenefit.objects.none()
        )
        year_packages = (
            SponsorshipPackage.objects.filter(year=selected_year)
            if selected_year
            else SponsorshipPackage.objects.none()
        )

        # Benefits grouped by program
        programs = SponsorshipProgram.objects.all().order_by("order")
        program_stats = []
        for program in programs:
            benefits = year_benefits.filter(program=program)
            if benefits.exists():
                program_stats.append(
                    {
                        "program": program,
                        "count": benefits.count(),
                        "unavailable": benefits.filter(unavailable=True).count(),
                        "new": benefits.filter(new=True).count(),
                        "total_value": benefits.aggregate(total=Sum("internal_value"))["total"] or 0,
                        "benefits": benefits.order_by("order"),
                    }
                )

        # Sponsorship stats for this year
        year_sponsorships = (
            Sponsorship.objects.filter(year=selected_year) if selected_year else Sponsorship.objects.none()
        )
        count_applied = year_sponsorships.filter(status=Sponsorship.APPLIED).count()
        count_approved = year_sponsorships.filter(status=Sponsorship.APPROVED).count()
        count_finalized = year_sponsorships.filter(status=Sponsorship.FINALIZED).count()
        count_rejected = year_sponsorships.filter(status=Sponsorship.REJECTED).count()

        # Action-needed lists
        needs_review = (
            year_sponsorships.filter(status=Sponsorship.APPLIED)
            .select_related("sponsor", "package")
            .order_by("applied_on")[:10]
        )
        pending_contracts = (
            year_sponsorships.filter(status=Sponsorship.APPROVED)
            .select_related("sponsor", "package")
            .order_by("approved_on")[:10]
        )

        # Revenue summary
        total_revenue = (
            year_sponsorships.filter(
                status__in=[Sponsorship.APPROVED, Sponsorship.FINALIZED],
            ).aggregate(total=Sum("sponsorship_fee"))["total"]
            or 0
        )

        context.update(
            {
                "years": years,
                "selected_year": selected_year,
                "current_year": current_year,
                "year_benefits": year_benefits,
                "year_packages": year_packages.order_by("-sponsorship_amount"),
                "program_stats": program_stats,
                "total_benefits": year_benefits.count(),
                "total_packages": year_packages.count(),
                "count_applied": count_applied,
                "count_approved": count_approved,
                "count_finalized": count_finalized,
                "count_rejected": count_rejected,
                "total_sponsorships": count_applied + count_approved + count_finalized + count_rejected,
                "total_revenue": total_revenue,
                "needs_review": needs_review,
                "pending_contracts": pending_contracts,
            }
        )
        return context


class BenefitListView(SponsorshipAdminRequiredMixin, ListView):
    """List benefits with filtering by year, program, package."""

    template_name = "sponsors/manage/benefit_list.html"
    context_object_name = "benefits"
    paginate_by = 50

    def get_queryset(self):
        """Return benefits filtered by year, program, and package."""
        qs = (
            SponsorshipBenefit.objects.select_related("program")
            .prefetch_related("packages")
            .order_by("-year", "program__order", "order")
        )

        self.filter_year = self.request.GET.get("year", "")
        self.filter_program = self.request.GET.get("program", "")
        self.filter_package = self.request.GET.get("package", "")

        if self.filter_year:
            qs = qs.filter(year=int(self.filter_year))
        if self.filter_program:
            qs = qs.filter(program_id=int(self.filter_program))
        if self.filter_package:
            qs = qs.filter(packages__id=int(self.filter_package))
        return qs

    def get_context_data(self, **kwargs):
        """Return context with benefit filter form."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = BenefitFilterForm(
            self.request.GET,
            selected_year=self.filter_year or None,
        )
        context["filter_year"] = self.filter_year
        context["filter_program"] = self.filter_program
        context["filter_package"] = self.filter_package
        return context


class BenefitCreateView(SponsorshipAdminRequiredMixin, CreateView):
    """Create a new sponsorship benefit."""

    model = SponsorshipBenefit
    form_class = SponsorshipBenefitManageForm
    template_name = "sponsors/manage/benefit_form.html"

    def get_success_url(self):
        """Return URL to benefit list filtered by year."""
        messages.success(self.request, f'Benefit "{self.object.name}" created successfully.')
        return reverse("manage_benefit_list") + f"?year={self.object.year}"

    def get_initial(self):
        """Return initial form data from query parameters."""
        initial = super().get_initial()
        year = self.request.GET.get("year")
        if year:
            initial["year"] = int(year)
        program = self.request.GET.get("program")
        if program:
            initial["program"] = int(program)
        return initial

    def get_context_data(self, **kwargs):
        """Return context with create flag."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context


class BenefitUpdateView(SponsorshipAdminRequiredMixin, UpdateView):
    """Edit an existing sponsorship benefit."""

    model = SponsorshipBenefit
    form_class = SponsorshipBenefitManageForm
    template_name = "sponsors/manage/benefit_form.html"

    def get_success_url(self):
        """Return URL to benefit list filtered by year."""
        messages.success(self.request, f'Benefit "{self.object.name}" updated successfully.')
        return reverse("manage_benefit_list") + f"?year={self.object.year}"

    def get_context_data(self, **kwargs):
        """Return context with related sponsorships, packages, and feature configurations."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        related = self.object.related_sponsorships.select_related("sponsor", "package").order_by("-year", "status")
        context["related_sponsorships"] = related
        context["related_sponsorships_count"] = related.count()
        context["benefit_packages"] = self.object.packages.order_by("order")
        # Feature configurations
        context["feature_configs"] = self.object.benefitfeatureconfiguration_set.all()
        context["config_types"] = CONFIG_TYPES
        return context


class BenefitDeleteView(SponsorshipAdminRequiredMixin, DeleteView):
    """Delete a sponsorship benefit."""

    model = SponsorshipBenefit
    template_name = "sponsors/manage/benefit_confirm_delete.html"

    def get_success_url(self):
        """Return URL to benefit list after deletion."""
        messages.success(self.request, f'Benefit "{self.object.name}" deleted.')
        year = self.object.year
        return reverse("manage_benefit_list") + (f"?year={year}" if year else "")


class PackageListView(SponsorshipAdminRequiredMixin, ListView):
    """List sponsorship packages grouped by year."""

    template_name = "sponsors/manage/package_list.html"
    context_object_name = "packages"

    def get_queryset(self):
        """Return packages optionally filtered by year."""
        qs = SponsorshipPackage.objects.order_by("-year", "-sponsorship_amount")
        self.filter_year = self.request.GET.get("year", "")
        if self.filter_year:
            qs = qs.filter(year=int(self.filter_year))
        return qs

    def get_context_data(self, **kwargs):
        """Return context with packages grouped by year."""
        context = super().get_context_data(**kwargs)
        years = SponsorshipPackage.objects.values_list("year", flat=True).distinct().order_by("-year")
        context["years"] = [y for y in years if y]
        context["filter_year"] = self.filter_year

        # Group packages by year for display
        packages_by_year = {}
        for pkg in context["packages"]:
            packages_by_year.setdefault(pkg.year, []).append(pkg)
        context["packages_by_year"] = dict(sorted(packages_by_year.items(), key=lambda x: x[0] or 0, reverse=True))
        return context


class PackageCreateView(SponsorshipAdminRequiredMixin, CreateView):
    """Create a new sponsorship package."""

    model = SponsorshipPackage
    form_class = SponsorshipPackageManageForm
    template_name = "sponsors/manage/package_form.html"

    def get_success_url(self):
        """Return URL to package list filtered by year."""
        messages.success(self.request, f'Package "{self.object.name}" created successfully.')
        return reverse("manage_packages") + f"?year={self.object.year}"

    def get_initial(self):
        """Return initial form data from query parameters."""
        initial = super().get_initial()
        year = self.request.GET.get("year")
        if year:
            initial["year"] = int(year)
        return initial

    def get_context_data(self, **kwargs):
        """Return context with create flag."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context


class PackageUpdateView(SponsorshipAdminRequiredMixin, UpdateView):
    """Edit an existing sponsorship package."""

    model = SponsorshipPackage
    form_class = SponsorshipPackageManageForm
    template_name = "sponsors/manage/package_form.html"

    def get_success_url(self):
        """Return URL to package list filtered by year."""
        messages.success(self.request, f'Package "{self.object.name}" updated successfully.')
        return reverse("manage_packages") + f"?year={self.object.year}"

    def get_context_data(self, **kwargs):
        """Return context with benefit count."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        context["benefit_count"] = self.object.benefits.count()
        return context


class PackageDeleteView(SponsorshipAdminRequiredMixin, DeleteView):
    """Delete a sponsorship package."""

    model = SponsorshipPackage
    template_name = "sponsors/manage/package_confirm_delete.html"

    def get_success_url(self):
        """Return URL to package list after deletion."""
        messages.success(self.request, f'Package "{self.object.name}" deleted.')
        year = self.object.year
        return reverse("manage_packages") + (f"?year={year}" if year else "")


class CloneYearView(SponsorshipAdminRequiredMixin, FormView):
    """Wizard to clone benefits and packages from one year to another."""

    template_name = "sponsors/manage/clone_year.html"
    form_class = CloneYearForm

    def get_context_data(self, **kwargs):
        """Return context with source year preview data."""
        context = super().get_context_data(**kwargs)
        # Preview data for the source year
        source_year = self.request.GET.get("source_year")
        if source_year:
            source_year = int(source_year)
            context["preview_benefits"] = (
                SponsorshipBenefit.objects.filter(year=source_year)
                .select_related("program")
                .order_by("program__order", "order")
            )
            context["preview_packages"] = SponsorshipPackage.objects.filter(year=source_year).order_by("order")
            context["source_year"] = source_year
        return context

    @transaction.atomic
    def form_valid(self, form):
        """Clone packages and benefits from source to target year."""
        source_year = int(form.cleaned_data["source_year"])
        target_year = form.cleaned_data["target_year"]
        clone_packages = form.cleaned_data["clone_packages"]
        clone_benefits = form.cleaned_data["clone_benefits"]

        cloned_packages = 0
        cloned_benefits = 0

        if clone_packages:
            for pkg in SponsorshipPackage.objects.filter(year=source_year):
                _, created = pkg.clone(target_year)
                if created:
                    cloned_packages += 1

        if clone_benefits:
            for benefit in SponsorshipBenefit.objects.filter(year=source_year):
                _, created = benefit.clone(target_year)
                if created:
                    cloned_benefits += 1

        messages.success(
            self.request,
            f"Cloned {cloned_packages} package(s) and {cloned_benefits} benefit(s) from {source_year} to {target_year}.",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Return URL to dashboard filtered by target year."""
        return reverse("manage_dashboard") + f"?year={self.request.POST.get('target_year', '')}"


class CurrentYearUpdateView(SponsorshipAdminRequiredMixin, UpdateView):
    """Update the active sponsorship year."""

    model = SponsorshipCurrentYear
    form_class = CurrentYearForm
    template_name = "sponsors/manage/current_year_form.html"

    def get_object(self, queryset=None):
        """Return the singleton current year object."""
        return SponsorshipCurrentYear.objects.first()

    def get_success_url(self):
        """Return URL to dashboard after update."""
        messages.success(self.request, f"Active year updated to {self.object.year}.")
        return reverse("manage_dashboard")


# ── Sponsorship Review Views ──────────────────────────────────────────


class SponsorshipListView(SponsorshipAdminRequiredMixin, ListView):
    """List sponsorships with filters for status, year, and search."""

    template_name = "sponsors/manage/sponsorship_list.html"
    context_object_name = "sponsorships"
    paginate_by = 30

    def get_queryset(self):
        """Return sponsorships filtered by status, year, and search term."""
        qs = Sponsorship.objects.select_related("sponsor", "package").order_by("-applied_on")

        self.filter_status = self.request.GET.get("status", "")
        self.filter_year = self.request.GET.get("year", "")
        self.filter_search = self.request.GET.get("search", "")

        qs = qs.filter(status=self.filter_status) if self.filter_status else qs.exclude(status=Sponsorship.REJECTED)
        if self.filter_year:
            qs = qs.filter(year=int(self.filter_year))
        if self.filter_search:
            qs = qs.filter(Q(sponsor__name__icontains=self.filter_search))
        return qs

    def get_context_data(self, **kwargs):
        """Return context with filter form and status counts."""
        context = super().get_context_data(**kwargs)
        context["filter_form"] = SponsorshipFilterForm(self.request.GET)
        context["filter_status"] = self.filter_status
        context["filter_year"] = self.filter_year
        context["filter_search"] = self.filter_search
        # Individual count vars for template
        context["count_applied"] = Sponsorship.objects.filter(status=Sponsorship.APPLIED).count()
        context["count_approved"] = Sponsorship.objects.filter(status=Sponsorship.APPROVED).count()
        context["count_finalized"] = Sponsorship.objects.filter(status=Sponsorship.FINALIZED).count()
        context["count_rejected"] = Sponsorship.objects.filter(status=Sponsorship.REJECTED).count()
        return context


class SponsorshipDetailView(SponsorshipAdminRequiredMixin, DetailView):
    """Detail view for reviewing a sponsorship application."""

    model = Sponsorship
    template_name = "sponsors/manage/sponsorship_detail.html"
    context_object_name = "sponsorship"

    def get_queryset(self):
        """Return sponsorships with related sponsor, package, and submitter."""
        return Sponsorship.objects.select_related("sponsor", "package", "submited_by")

    def get_context_data(self, **kwargs):
        """Return context with benefits, contacts, and status flags."""
        context = super().get_context_data(**kwargs)
        sp = self.object
        context["benefits"] = sp.benefits.select_related("program", "sponsorship_benefit").order_by(
            "program__order", "order"
        )
        context["contacts"] = sp.sponsor.contacts.all() if sp.sponsor else []
        context["can_approve"] = Sponsorship.APPROVED in sp.next_status
        context["can_reject"] = Sponsorship.REJECTED in sp.next_status
        context["can_rollback"] = (
            sp.status in [Sponsorship.APPLIED, Sponsorship.APPROVED, Sponsorship.REJECTED]
            and sp.status != Sponsorship.FINALIZED
        )
        context["can_unlock"] = sp.locked and sp.status == Sponsorship.FINALIZED
        context["can_lock"] = not sp.locked and sp.status != Sponsorship.APPLIED
        # Contract info
        try:
            context["contract"] = sp.contract
        except Contract.DoesNotExist:
            context["contract"] = None
        # Required assets
        required_assets = list(BenefitFeature.objects.required_assets().from_sponsorship(sp))
        assets_submitted = 0
        for asset in required_assets:
            with contextlib.suppress(Exception):
                val = asset.value
                if val and (not hasattr(val, "url") or val.url):
                    assets_submitted += 1
        context["required_assets"] = required_assets
        context["assets_submitted"] = assets_submitted
        context["assets_total"] = len(required_assets)
        # Benefit add form (only when editable)
        if sp.open_for_editing:
            context["add_benefit_form"] = AddBenefitToSponsorshipForm(sponsorship=sp)
        return context


class SponsorshipApproveView(SponsorshipAdminRequiredMixin, UpdateView):
    """Approve a sponsorship application with date/fee/package form."""

    model = Sponsorship
    form_class = SponsorshipApproveForm
    template_name = "sponsors/manage/sponsorship_approve.html"

    def get_queryset(self):
        """Return sponsorships with related sponsor and package."""
        return Sponsorship.objects.select_related("sponsor", "package")

    def get_initial(self):
        """Return initial form data from the sponsorship instance."""
        return {
            "package": self.object.package,
            "start_date": self.object.start_date,
            "end_date": self.object.end_date,
            "sponsorship_fee": self.object.sponsorship_fee,
        }

    def get_context_data(self, **kwargs):
        """Return context with previous effective date."""
        context = super().get_context_data(**kwargs)
        context["previous_effective"] = self.object.previous_effective_date
        return context

    def form_valid(self, form):
        """Approve the sponsorship and redirect to detail."""
        sp = self.object
        try:
            kwargs = form.cleaned_data
            kwargs["request"] = self.request
            use_case = use_cases.ApproveSponsorshipApplicationUseCase.build()
            use_case.execute(sp, **kwargs)
            messages.success(self.request, f'Sponsorship for "{sp.sponsor.name}" approved.')
        except InvalidStatusError as e:
            messages.error(self.request, str(e))
        return redirect(reverse("manage_sponsorship_detail", args=[sp.pk]))


class SponsorshipApproveSignedView(SponsorshipAdminRequiredMixin, View):
    """Approve a sponsorship and execute contract with an already-signed document."""

    def get(self, request, pk):
        """Render the approve-with-signed-contract form."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor", "package"), pk=pk)
        form = SponsorshipApproveSignedForm(
            instance=sp,
            initial={
                "package": sp.package,
                "start_date": sp.start_date,
                "end_date": sp.end_date,
                "sponsorship_fee": sp.sponsorship_fee,
            },
        )
        context = {
            "sponsorship": sp,
            "form": form,
            "previous_effective": sp.previous_effective_date,
        }
        return render(request, "sponsors/manage/sponsorship_approve_signed.html", context)

    def post(self, request, pk):
        """Approve sponsorship and execute the uploaded signed contract."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor", "package"), pk=pk)
        form = SponsorshipApproveSignedForm(request.POST, request.FILES, instance=sp)
        if form.is_valid():
            kwargs = form.cleaned_data
            kwargs["request"] = request
            try:
                # Approve the sponsorship and create a draft contract
                use_case = use_cases.ApproveSponsorshipApplicationUseCase.build()
                sp = use_case.execute(sp, **kwargs)
                # Execute it with the uploaded signed contract
                use_case = use_cases.ExecuteExistingContractUseCase.build()
                use_case.execute(sp.contract, kwargs["signed_contract"], request=request)
                messages.success(request, f'Sponsorship for "{sp.sponsor.name}" approved with signed contract.')
            except InvalidStatusError as e:
                messages.error(request, str(e))
            return redirect(reverse("manage_sponsorship_detail", args=[sp.pk]))

        context = {
            "sponsorship": sp,
            "form": form,
            "previous_effective": sp.previous_effective_date,
        }
        return render(request, "sponsors/manage/sponsorship_approve_signed.html", context)


class AssetExportView(SponsorshipAdminRequiredMixin, View):
    """Export required assets for a sponsorship as a ZIP file."""

    def get(self, request, pk):
        """Generate and return a ZIP of all submitted assets for the sponsorship."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor"), pk=pk)
        assets = list(BenefitFeature.objects.required_assets().from_sponsorship(sp))

        # Filter to only assets that have values
        assets_with_values = [a for a in assets if a.has_value]
        if not assets_with_values:
            messages.warning(request, "No submitted assets to export.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))

        sponsor_name = sp.sponsor.name if sp.sponsor else "unknown"
        buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(buffer, "w")

        for asset in assets_with_values:
            if not asset.is_file:
                zip_file.writestr(f"{sponsor_name}/{asset.internal_name}.txt", asset.value)
            else:
                suffix = "." + asset.value.name.split(".")[-1]
                prefix = asset.internal_name
                with NamedTemporaryFile(suffix=suffix, prefix=prefix) as temp_file:
                    temp_file.write(asset.value.read())
                    zip_file.write(temp_file.name, arcname=f"{sponsor_name}/{prefix}{suffix}")

        zip_file.close()
        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = f'attachment; filename="{sponsor_name}-assets.zip"'
        return response


class BulkAssetExportView(SponsorshipAdminRequiredMixin, View):
    """Export assets for multiple sponsorships as a ZIP file (bulk action)."""

    def post(self, request):
        """Generate and return a ZIP of all submitted assets for selected sponsorships."""
        selected_ids = request.POST.getlist("selected_ids")
        if not selected_ids:
            messages.warning(request, "No sponsorships selected.")
            return redirect(reverse("manage_sponsorships"))

        sponsorships = Sponsorship.objects.select_related("sponsor").filter(pk__in=selected_ids)
        if not sponsorships.exists():
            messages.warning(request, "No sponsorships found.")
            return redirect(reverse("manage_sponsorships"))

        buffer = io.BytesIO()
        zip_file = zipfile.ZipFile(buffer, "w")
        total_assets = 0

        for sp in sponsorships:
            assets = list(BenefitFeature.objects.required_assets().from_sponsorship(sp))
            sponsor_name = sp.sponsor.name if sp.sponsor else "unknown"

            for asset in assets:
                if not asset.has_value:
                    continue
                total_assets += 1
                if not asset.is_file:
                    zip_file.writestr(f"{sponsor_name}/{asset.internal_name}.txt", asset.value)
                else:
                    suffix = "." + asset.value.name.split(".")[-1]
                    prefix = asset.internal_name
                    with NamedTemporaryFile(suffix=suffix, prefix=prefix) as temp_file:
                        temp_file.write(asset.value.read())
                        zip_file.write(temp_file.name, arcname=f"{sponsor_name}/{prefix}{suffix}")

        zip_file.close()

        if total_assets == 0:
            messages.warning(request, "No submitted assets found for the selected sponsorships.")
            return redirect(reverse("manage_sponsorships"))

        response = HttpResponse(buffer.getvalue())
        response["Content-Type"] = "application/x-zip-compressed"
        response["Content-Disposition"] = 'attachment; filename="sponsorship-assets.zip"'
        return response


class SponsorshipRejectView(SponsorshipAdminRequiredMixin, View):
    """Reject a sponsorship application."""

    def post(self, request, pk):
        """Reject the sponsorship application."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        try:
            use_case = use_cases.RejectSponsorshipApplicationUseCase.build()
            use_case.execute(sp)
            messages.success(request, f'Sponsorship for "{sp.sponsor.name}" rejected.')
        except InvalidStatusError as e:
            messages.error(request, str(e))
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


class SponsorshipRollbackView(SponsorshipAdminRequiredMixin, View):
    """Roll back a sponsorship to editing/applied status."""

    def post(self, request, pk):
        """Roll back sponsorship to editing status."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        try:
            sp.rollback_to_editing()
            sp.save()
            messages.success(request, f'Sponsorship for "{sp.sponsor.name}" rolled back to editing.')
        except InvalidStatusError as e:
            messages.error(request, str(e))
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


class SponsorshipLockToggleView(SponsorshipAdminRequiredMixin, View):
    """Toggle lock/unlock on a sponsorship."""

    def post(self, request, pk):
        """Toggle the lock state of a sponsorship."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        action = request.POST.get("action")
        if action == "lock":
            sp.locked = True
            sp.save(update_fields=["locked"])
            messages.success(request, "Sponsorship locked.")
        elif action == "unlock":
            sp.locked = False
            sp.save(update_fields=["locked"])
            messages.success(request, "Sponsorship unlocked.")
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


class SponsorshipEditView(SponsorshipAdminRequiredMixin, UpdateView):
    """Edit sponsorship details (package, fee, year)."""

    model = Sponsorship
    form_class = SponsorshipEditForm
    template_name = "sponsors/manage/sponsorship_edit.html"

    def get_queryset(self):
        """Return sponsorships with related sponsor and package."""
        return Sponsorship.objects.select_related("sponsor", "package")

    def get_success_url(self):
        """Return URL to sponsorship detail after update."""
        messages.success(self.request, "Sponsorship updated.")
        return reverse("manage_sponsorship_detail", args=[self.object.pk])


class SponsorCreateView(SponsorshipAdminRequiredMixin, CreateView):
    """Create a new sponsor (standalone, not via composer)."""

    model = Sponsor
    form_class = SponsorEditForm
    template_name = "sponsors/manage/sponsor_edit.html"

    def get_context_data(self, **kwargs):
        """Return context with create flag."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        return context

    def get_success_url(self):
        """Return URL to sponsor edit page to add contacts etc."""
        messages.success(
            self.request,
            f'Sponsor "{self.object.name}" created. Add contacts or start a sponsorship.',
        )
        return reverse("manage_sponsor_edit", args=[self.object.pk])


class SponsorEditView(SponsorshipAdminRequiredMixin, UpdateView):
    """Edit sponsor company details."""

    model = Sponsor
    form_class = SponsorEditForm
    template_name = "sponsors/manage/sponsor_edit.html"

    def get_context_data(self, **kwargs):
        """Return context with originating sponsorship reference."""
        context = super().get_context_data(**kwargs)
        sp_pk = self.request.GET.get("from_sponsorship")
        if sp_pk:
            context["from_sponsorship"] = sp_pk
        return context

    def get_success_url(self):
        """Return URL to sponsorship detail or sponsor list."""
        messages.success(self.request, f'Sponsor "{self.object.name}" updated.')
        sp_pk = self.request.POST.get("from_sponsorship") or self.request.GET.get("from_sponsorship")
        if sp_pk:
            return reverse("manage_sponsorship_detail", args=[sp_pk])
        return reverse("manage_sponsorships")


# ── Benefit management on sponsorships ────────────────────────────────


class SponsorshipAddBenefitView(SponsorshipAdminRequiredMixin, View):
    """Add a benefit to a sponsorship."""

    def post(self, request, pk):
        """Add a selected benefit to the sponsorship."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        if not sp.open_for_editing:
            messages.error(request, "Sponsorship is locked and cannot be edited.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))

        form = AddBenefitToSponsorshipForm(request.POST, sponsorship=sp)
        if form.is_valid():
            benefit = form.cleaned_data["benefit"]
            SponsorBenefit.new_copy(benefit, sponsorship=sp, added_by_user=True)
            messages.success(request, f'Added "{benefit.name}" to sponsorship.')
        else:
            messages.error(request, "Invalid benefit selection.")
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


class SponsorshipRemoveBenefitView(SponsorshipAdminRequiredMixin, View):
    """Remove a benefit from a sponsorship."""

    def post(self, request, pk, benefit_pk):
        """Remove a benefit from the sponsorship."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        if not sp.open_for_editing:
            messages.error(request, "Sponsorship is locked and cannot be edited.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))

        benefit = get_object_or_404(SponsorBenefit, pk=benefit_pk, sponsorship=sp)
        name = benefit.name
        benefit.delete()
        messages.success(request, f'Removed "{name}" from sponsorship.')
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


# ── Contract management ───────────────────────────────────────────────


class ContractPreviewView(SponsorshipAdminRequiredMixin, View):
    """Preview/download a contract as PDF or DOCX."""

    def get(self, request, pk):
        """Render contract preview in the requested format."""
        from apps.sponsors.contracts import render_contract_to_docx_response, render_contract_to_pdf_response

        sp = get_object_or_404(Sponsorship, pk=pk)
        try:
            contract = sp.contract
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))

        output_format = request.GET.get("format", "pdf")
        if output_format == "docx":
            response = render_contract_to_docx_response(request, contract)
        else:
            response = render_contract_to_pdf_response(request, contract)
        response["X-Frame-Options"] = "SAMEORIGIN"
        return response


class ContractSendView(SponsorshipAdminRequiredMixin, View):
    """Generate contract and send to sponsor or internal review."""

    def get(self, request, pk):
        """Render the contract send page with both options."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor"), pk=pk)
        try:
            contract = sp.contract
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists for this sponsorship.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))
        context = {
            "sponsorship": sp,
            "contract": contract,
            "sponsor_emails": sp.verified_emails if sp.sponsor else [],
            "internal_email": request.GET.get("internal_email", ""),
        }
        return render(request, "sponsors/manage/contract_send.html", context)

    def post(self, request, pk):
        """Handle send to sponsor or internal review."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        action = request.POST.get("action", "")

        try:
            contract = sp.contract
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))

        handler = {
            "generate": self._handle_generate,
            "send_sponsor": self._handle_send_sponsor,
            "send_internal": self._handle_send_internal,
        }.get(action)

        if handler:
            return handler(request, sp, contract)

        messages.error(request, "Unknown action.")
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))

    @staticmethod
    def _handle_generate(request, sp, contract):
        try:
            use_case = use_cases.SendContractUseCase.build()
            use_case.execute(contract, request=request)
            messages.success(request, "Contract generated and finalized. Ready to send.")
        except InvalidStatusError as e:
            messages.error(request, str(e))
        return redirect(reverse("manage_contract_send", args=[sp.pk]))

    @staticmethod
    def _handle_send_sponsor(request, sp, contract):
        from apps.sponsors.notifications import ContractNotificationToSponsors

        if not contract.document:
            messages.error(request, "Generate the contract first before sending to sponsor.")
            return redirect(reverse("manage_contract_send", args=[sp.pk]))
        notification = ContractNotificationToSponsors()
        notification.notify(contract=contract, request=request)
        recipient_list = ", ".join(sp.verified_emails)
        messages.success(request, f"Contract sent to sponsor ({recipient_list}).")
        return redirect(reverse("manage_sponsorship_detail", args=[sp.pk]))

    @staticmethod
    def _handle_send_internal(request, sp, contract):
        from django.core.mail import EmailMessage

        from apps.sponsors.contracts import render_contract_to_docx_file, render_contract_to_pdf_file

        internal_email = request.POST.get("internal_email", "").strip()
        if not internal_email:
            messages.error(request, "Please enter an email address.")
            return redirect(reverse("manage_contract_send", args=[sp.pk]))

        email = EmailMessage(
            subject=f"[Internal Review] Contract for {sp.sponsor.name}",
            body=f"Contract for {sp.sponsor.name} ({sp.level_name}, ${sp.sponsorship_fee}) attached for review.",
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
            to=[internal_email],
        )

        # Use stored files if available, otherwise render live
        pdf_content = None
        if contract.document:
            try:
                with contract.document.open("rb") as f:
                    pdf_content = f.read()
            except FileNotFoundError:
                pass
        if not pdf_content:
            pdf_content = render_contract_to_pdf_file(contract)

        if pdf_content:
            email.attach("Contract.pdf", pdf_content, "application/pdf")

        docx_content = None
        if contract.document_docx:
            try:
                with contract.document_docx.open("rb") as f:
                    docx_content = f.read()
            except FileNotFoundError:
                pass
        if not docx_content:
            docx_content = render_contract_to_docx_file(contract)

        if docx_content:
            email.attach(
                "Contract.docx",
                docx_content,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )

        email.send()
        messages.success(request, f"Contract sent to {internal_email} for internal review.")
        return redirect(reverse("manage_sponsorship_detail", args=[sp.pk]))


class ContractExecuteView(SponsorshipAdminRequiredMixin, View):
    """Upload signed document and execute contract."""

    def get(self, request, pk):
        """Render the contract execution form."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor"), pk=pk)
        try:
            contract = sp.contract
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))
        form = ExecuteContractForm()
        context = {"sponsorship": sp, "contract": contract, "form": form}
        return render(request, "sponsors/manage/contract_execute.html", context)

    def post(self, request, pk):
        """Upload signed document and execute the contract."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        form = ExecuteContractForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                contract = sp.contract
                signed_doc = form.cleaned_data["signed_document"]
                use_case = use_cases.ExecuteContractUseCase.build()
                use_case.execute(contract, signed_doc, request=request)
                messages.success(request, "Contract executed. Sponsorship finalized.")
            except Contract.DoesNotExist:
                messages.error(request, "No contract exists.")
            except InvalidStatusError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please upload the signed document.")
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


class ContractNullifyView(SponsorshipAdminRequiredMixin, View):
    """Nullify/void a contract."""

    def post(self, request, pk):
        """Nullify the contract and redirect to detail."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        try:
            contract = sp.contract
            use_case = use_cases.NullifyContractUseCase.build()
            use_case.execute(contract, request=request)
            messages.success(request, "Contract nullified.")
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists.")
        except InvalidStatusError as e:
            messages.error(request, str(e))
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


class ContractRedraftView(SponsorshipAdminRequiredMixin, View):
    """Re-draft a nullified contract, creating a new revision."""

    def post(self, request, pk):
        """Transition contract from nullified back to draft."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        try:
            contract = sp.contract
            if Contract.DRAFT not in contract.next_status:
                messages.error(request, f"Cannot re-draft a {contract.get_status_display()} contract.")
            else:
                contract.status = Contract.DRAFT
                contract.save()
                messages.success(request, f"Contract re-drafted (Revision {contract.revision}).")
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists.")
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


# ── Notification views ────────────────────────────────────────────────


class SponsorshipNotifyView(SponsorshipAdminRequiredMixin, View):
    """Send a notification to sponsor contacts for a specific sponsorship."""

    def get(self, request, pk):
        """Render the notification form with optional preview."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor"), pk=pk)
        form = SendSponsorshipNotificationManageForm()
        context = {
            "sponsorship": sp,
            "form": form,
            "email_preview": None,
            "template_vars": NOTIFICATION_TEMPLATE_VARS,
        }
        return render(request, "sponsors/manage/sponsorship_notify.html", context)

    def post(self, request, pk):
        """Preview or send the notification."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor"), pk=pk)
        form = SendSponsorshipNotificationManageForm(request.POST)
        email_preview = None

        if "preview" in request.POST:
            if form.is_valid():
                notification = form.get_notification()
                msg_kwargs = {
                    "to_primary": True,
                    "to_administrative": True,
                    "to_accounting": True,
                    "to_manager": True,
                }
                email_preview = notification.get_email_message(sp, **msg_kwargs)
            context = {
                "sponsorship": sp,
                "form": form,
                "email_preview": email_preview,
                "template_vars": NOTIFICATION_TEMPLATE_VARS,
            }
            return render(request, "sponsors/manage/sponsorship_notify.html", context)

        if "confirm" in request.POST and form.is_valid():
            use_case = use_cases.SendSponsorshipNotificationUseCase.build()
            use_case.execute(
                notification=form.get_notification(),
                sponsorships=[sp],
                contact_types=form.cleaned_data["contact_types"],
                request=request,
            )
            messages.success(request, f"Notification sent to {sp.sponsor.name} contacts.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))

        context = {
            "sponsorship": sp,
            "form": form,
            "email_preview": email_preview,
            "template_vars": NOTIFICATION_TEMPLATE_VARS,
        }
        return render(request, "sponsors/manage/sponsorship_notify.html", context)


# ── Notification template CRUD ────────────────────────────────────────


class NotificationTemplateListView(SponsorshipAdminRequiredMixin, ListView):
    """List all SponsorEmailNotificationTemplate instances."""

    model = SponsorEmailNotificationTemplate
    template_name = "sponsors/manage/notification_template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        """Return templates ordered by most recently updated."""
        return SponsorEmailNotificationTemplate.objects.order_by("-updated_at")


NOTIFICATION_TEMPLATE_VARS = [
    "sponsor_name",
    "sponsorship_level",
    "sponsorship_start_date",
    "sponsorship_end_date",
    "sponsorship_status",
]


class NotificationTemplateCreateView(SponsorshipAdminRequiredMixin, CreateView):
    """Create a new notification template."""

    model = SponsorEmailNotificationTemplate
    form_class = NotificationTemplateForm
    template_name = "sponsors/manage/notification_template_form.html"

    def get_success_url(self):
        """Return URL to template list after creation."""
        messages.success(self.request, f'Template "{self.object.internal_name}" created.')
        return reverse("manage_notification_templates")

    def get_context_data(self, **kwargs):
        """Return context with create flag and template variables."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = True
        context["template_vars"] = NOTIFICATION_TEMPLATE_VARS
        return context


class NotificationTemplateUpdateView(SponsorshipAdminRequiredMixin, UpdateView):
    """Edit an existing notification template."""

    model = SponsorEmailNotificationTemplate
    form_class = NotificationTemplateForm
    template_name = "sponsors/manage/notification_template_form.html"

    def get_success_url(self):
        """Return URL to template list after update."""
        messages.success(self.request, f'Template "{self.object.internal_name}" updated.')
        return reverse("manage_notification_templates")

    def get_context_data(self, **kwargs):
        """Return context with edit flag and template variables."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        context["template_vars"] = NOTIFICATION_TEMPLATE_VARS
        return context


class NotificationTemplateDeleteView(SponsorshipAdminRequiredMixin, DeleteView):
    """Delete a notification template."""

    model = SponsorEmailNotificationTemplate
    template_name = "sponsors/manage/notification_template_confirm_delete.html"

    def get_success_url(self):
        """Return URL to template list after deletion."""
        messages.success(self.request, f'Template "{self.object.internal_name}" deleted.')
        return reverse("manage_notification_templates")


# ── Sponsor contact management ───────────────────────────────────────


class SponsorContactCreateView(SponsorshipAdminRequiredMixin, CreateView):
    """Add a contact to a sponsor."""

    model = SponsorContact
    form_class = SponsorContactForm
    template_name = "sponsors/manage/contact_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Look up the sponsor from the URL."""
        self.sponsor = get_object_or_404(Sponsor, pk=kwargs["sponsor_pk"])
        self.from_sponsorship = request.GET.get("from_sponsorship", "")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return context with sponsor and create flag."""
        context = super().get_context_data(**kwargs)
        context["sponsor"] = self.sponsor
        context["is_create"] = True
        context["from_sponsorship"] = self.from_sponsorship
        return context

    def form_valid(self, form):
        """Set sponsor on the contact before saving."""
        form.instance.sponsor = self.sponsor
        return super().form_valid(form)

    def get_success_url(self):
        """Return URL back to sponsorship detail or sponsor edit."""
        messages.success(self.request, f'Contact "{self.object.name}" added.')
        if self.from_sponsorship:
            return reverse("manage_sponsorship_detail", args=[self.from_sponsorship])
        return reverse("manage_sponsor_edit", args=[self.sponsor.pk])


class SponsorContactUpdateView(SponsorshipAdminRequiredMixin, UpdateView):
    """Edit a sponsor contact."""

    model = SponsorContact
    form_class = SponsorContactForm
    template_name = "sponsors/manage/contact_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Store from_sponsorship for redirect."""
        self.from_sponsorship = request.GET.get("from_sponsorship", "")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return context with sponsor and edit flag."""
        context = super().get_context_data(**kwargs)
        context["sponsor"] = self.object.sponsor
        context["is_create"] = False
        context["from_sponsorship"] = self.from_sponsorship
        return context

    def get_success_url(self):
        """Return URL back to sponsorship detail or sponsor edit."""
        messages.success(self.request, f'Contact "{self.object.name}" updated.')
        if self.from_sponsorship:
            return reverse("manage_sponsorship_detail", args=[self.from_sponsorship])
        return reverse("manage_sponsor_edit", args=[self.object.sponsor.pk])


class SponsorContactDeleteView(SponsorshipAdminRequiredMixin, View):
    """Delete a sponsor contact."""

    def post(self, request, pk):
        """Delete the contact and redirect."""
        contact = get_object_or_404(SponsorContact, pk=pk)
        name = contact.name
        sponsor_pk = contact.sponsor_id
        from_sp = request.POST.get("from_sponsorship", "")
        contact.delete()
        messages.success(request, f'Contact "{name}" deleted.')
        if from_sp:
            return redirect(reverse("manage_sponsorship_detail", args=[from_sp]))
        return redirect(reverse("manage_sponsor_edit", args=[sponsor_pk]))


# ── CSV Export & Bulk Actions ─────────────────────────────────────────


def _filtered_sponsorship_queryset(request):
    """Build a Sponsorship queryset from request query params.

    Applies the same filters as SponsorshipListView: status, year, search.
    """
    qs = Sponsorship.objects.select_related("sponsor", "package").order_by("-applied_on")

    status = request.GET.get("status", "") or request.POST.get("status", "")
    year = request.GET.get("year", "") or request.POST.get("year", "")
    search = request.GET.get("search", "") or request.POST.get("search", "")

    qs = qs.filter(status=status) if status else qs.exclude(status=Sponsorship.REJECTED)
    if year:
        qs = qs.filter(year=int(year))
    if search:
        qs = qs.filter(Q(sponsor__name__icontains=search))

    return qs


def _write_sponsorship_csv(sponsorships, response):
    """Write sponsorship rows to a CSV response using csv.writer."""
    writer = csv.writer(response)
    writer.writerow(
        [
            "Sponsor Name",
            "Package",
            "Fee",
            "Year",
            "Status",
            "Applied Date",
            "Start Date",
            "End Date",
            "Primary Contact Name",
            "Primary Contact Email",
        ]
    )
    # Pre-fetch primary contacts for all sponsors in one query
    sponsor_ids = [sp.sponsor_id for sp in sponsorships if sp.sponsor_id]
    primary_contacts = {}
    if sponsor_ids:
        for contact in SponsorContact.objects.filter(sponsor_id__in=sponsor_ids, primary=True):
            # Keep the first primary contact per sponsor
            primary_contacts.setdefault(contact.sponsor_id, contact)

    for sp in sponsorships:
        contact = primary_contacts.get(sp.sponsor_id) if sp.sponsor_id else None
        writer.writerow(
            [
                sp.sponsor.name if sp.sponsor else "Unknown",
                sp.package.name if sp.package else "",
                sp.sponsorship_fee or "",
                sp.year or "",
                sp.get_status_display(),
                sp.applied_on.isoformat() if sp.applied_on else "",
                sp.start_date.isoformat() if sp.start_date else "",
                sp.end_date.isoformat() if sp.end_date else "",
                contact.name if contact else "",
                contact.email if contact else "",
            ]
        )
    return response


class SponsorshipExportView(SponsorshipAdminRequiredMixin, View):
    """Export sponsorships as CSV for accounting.

    Supports both GET (with filter query params) and POST (with selected_ids
    for bulk export of specific sponsorships).
    """

    def get(self, request):
        """Export all sponsorships matching current filters."""
        sponsorships = list(_filtered_sponsorship_queryset(request))
        return self._make_csv(sponsorships)

    def post(self, request):
        """Export specific sponsorships by selected IDs."""
        selected_ids = request.POST.getlist("selected_ids")
        if selected_ids:
            sponsorships = list(
                Sponsorship.objects.select_related("sponsor", "package")
                .filter(pk__in=selected_ids)
                .order_by("-applied_on")
            )
        else:
            sponsorships = list(_filtered_sponsorship_queryset(request))
        return self._make_csv(sponsorships)

    def _make_csv(self, sponsorships):
        """Build and return an HttpResponse with CSV content."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="sponsorships.csv"'
        return _write_sponsorship_csv(sponsorships, response)


class BulkActionDispatchView(SponsorshipAdminRequiredMixin, View):
    """Dispatch bulk actions from the sponsorship list.

    Routes to the appropriate handler based on the ``action`` field:
    - ``export_csv``: export selected sponsorships as CSV
    - ``send_notification``: redirect to bulk notification page
    """

    def post(self, request):
        """Route to the correct bulk action."""
        action = request.POST.get("action", "")
        selected_ids = request.POST.getlist("selected_ids")

        if action == "export_csv":
            if selected_ids:
                sponsorships = list(
                    Sponsorship.objects.select_related("sponsor", "package")
                    .filter(pk__in=selected_ids)
                    .order_by("-applied_on")
                )
            else:
                messages.warning(request, "No sponsorships selected.")
                return redirect(reverse("manage_sponsorships"))
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="sponsorships.csv"'
            return _write_sponsorship_csv(sponsorships, response)

        if action == "send_notification":
            if not selected_ids:
                messages.warning(request, "No sponsorships selected.")
                return redirect(reverse("manage_sponsorships"))
            request.session["bulk_notify_ids"] = selected_ids
            return redirect(reverse("manage_bulk_notify"))

        if action == "export_assets":
            return BulkAssetExportView.as_view()(request)

        messages.error(request, "Unknown action.")
        return redirect(reverse("manage_sponsorships"))


class BulkNotifyView(SponsorshipAdminRequiredMixin, View):
    """Send a notification to contacts for multiple sponsorships at once."""

    def get(self, request):
        """Render the bulk notification form."""
        ids = request.session.get("bulk_notify_ids", [])
        sponsorships = list(Sponsorship.objects.select_related("sponsor").filter(pk__in=ids).order_by("-applied_on"))
        if not sponsorships:
            messages.warning(request, "No sponsorships selected for notification.")
            return redirect(reverse("manage_sponsorships"))
        form = SendSponsorshipNotificationManageForm()
        context = {
            "sponsorships": sponsorships,
            "form": form,
            "email_preview": None,
            "template_vars": NOTIFICATION_TEMPLATE_VARS,
        }
        return render(request, "sponsors/manage/bulk_notify.html", context)

    def post(self, request):
        """Preview or send bulk notification."""
        ids = request.session.get("bulk_notify_ids", [])
        sponsorships = list(Sponsorship.objects.select_related("sponsor").filter(pk__in=ids).order_by("-applied_on"))
        if not sponsorships:
            messages.warning(request, "No sponsorships selected for notification.")
            return redirect(reverse("manage_sponsorships"))

        form = SendSponsorshipNotificationManageForm(request.POST)
        email_preview = None

        if "preview" in request.POST:
            if form.is_valid():
                notification = form.get_notification()
                msg_kwargs = {
                    "to_primary": True,
                    "to_administrative": True,
                    "to_accounting": True,
                    "to_manager": True,
                }
                # Preview using the first sponsorship
                email_preview = notification.get_email_message(sponsorships[0], **msg_kwargs)
            context = {
                "sponsorships": sponsorships,
                "form": form,
                "email_preview": email_preview,
                "template_vars": NOTIFICATION_TEMPLATE_VARS,
            }
            return render(request, "sponsors/manage/bulk_notify.html", context)

        if "confirm" in request.POST and form.is_valid():
            use_case = use_cases.SendSponsorshipNotificationUseCase.build()
            use_case.execute(
                notification=form.get_notification(),
                sponsorships=sponsorships,
                contact_types=form.cleaned_data["contact_types"],
                request=request,
            )
            # Clear session data
            request.session.pop("bulk_notify_ids", None)
            names = ", ".join(sp.sponsor.name for sp in sponsorships if sp.sponsor)
            messages.success(request, f"Notification sent to {len(sponsorships)} sponsor(s): {names}.")
            return redirect(reverse("manage_sponsorships"))

        context = {
            "sponsorships": sponsorships,
            "form": form,
            "email_preview": email_preview,
            "template_vars": NOTIFICATION_TEMPLATE_VARS,
        }
        return render(request, "sponsors/manage/bulk_notify.html", context)


# ── Benefit Feature Configuration management ─────────────────────────


def _get_config_type_slug(config_instance):
    """Return the CONFIG_TYPES slug for a polymorphic config instance."""
    for slug, (model_cls, _form_cls, _label) in CONFIG_TYPES.items():
        if isinstance(config_instance, model_cls):
            return slug
    return None


class BenefitConfigAddView(SponsorshipAdminRequiredMixin, View):
    """Add a feature configuration to a benefit."""

    def dispatch(self, request, *args, **kwargs):
        """Look up the benefit and validate the config type."""
        self.benefit = get_object_or_404(SponsorshipBenefit, pk=kwargs["pk"])
        self.config_type = kwargs["config_type"]
        if self.config_type not in CONFIG_TYPES:
            messages.error(request, f"Unknown configuration type: {self.config_type}")
            return redirect(reverse("manage_benefit_edit", args=[self.benefit.pk]))
        self.model_cls, self.form_cls, self.type_label = CONFIG_TYPES[self.config_type]
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk, config_type):
        """Render the add configuration form."""
        form = self.form_cls()
        context = {
            "benefit": self.benefit,
            "form": form,
            "type_label": self.type_label,
            "is_create": True,
        }
        return render(request, "sponsors/manage/benefit_config_form.html", context)

    def post(self, request, pk, config_type):
        """Create the configuration and redirect to benefit edit."""
        form = self.form_cls(request.POST, request.FILES)
        if form.is_valid():
            config = form.save(commit=False)
            config.benefit = self.benefit
            config.save()
            messages.success(request, f"{self.type_label} configuration added.")
            return redirect(reverse("manage_benefit_edit", args=[self.benefit.pk]))
        context = {
            "benefit": self.benefit,
            "form": form,
            "type_label": self.type_label,
            "is_create": True,
        }
        return render(request, "sponsors/manage/benefit_config_form.html", context)


class BenefitConfigEditView(SponsorshipAdminRequiredMixin, View):
    """Edit an existing feature configuration."""

    def dispatch(self, request, *args, **kwargs):
        """Look up the config instance and resolve its polymorphic form."""
        self.config = get_object_or_404(BenefitFeatureConfiguration, pk=kwargs["pk"])
        self.config_slug = _get_config_type_slug(self.config)
        if not self.config_slug:
            messages.error(request, "Unknown configuration type.")
            return redirect(reverse("manage_benefit_edit", args=[self.config.benefit_id]))
        _model_cls, self.form_cls, self.type_label = CONFIG_TYPES[self.config_slug]
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        """Render the edit configuration form."""
        form = self.form_cls(instance=self.config)
        context = {
            "benefit": self.config.benefit,
            "form": form,
            "type_label": self.type_label,
            "is_create": False,
            "config": self.config,
        }
        return render(request, "sponsors/manage/benefit_config_form.html", context)

    def post(self, request, pk):
        """Update the configuration and redirect to benefit edit."""
        form = self.form_cls(request.POST, request.FILES, instance=self.config)
        if form.is_valid():
            form.save()
            messages.success(request, f"{self.type_label} configuration updated.")
            return redirect(reverse("manage_benefit_edit", args=[self.config.benefit_id]))
        context = {
            "benefit": self.config.benefit,
            "form": form,
            "type_label": self.type_label,
            "is_create": False,
            "config": self.config,
        }
        return render(request, "sponsors/manage/benefit_config_form.html", context)


class BenefitConfigDeleteView(SponsorshipAdminRequiredMixin, View):
    """Delete a feature configuration (POST only)."""

    def post(self, request, pk):
        """Delete the configuration and redirect to benefit edit."""
        config = get_object_or_404(BenefitFeatureConfiguration, pk=pk)
        benefit_pk = config.benefit_id
        config.delete()
        messages.success(request, "Configuration deleted.")
        return redirect(reverse("manage_benefit_edit", args=[benefit_pk]))


class ComposerView(SponsorshipAdminRequiredMixin, View):
    """Multi-step wizard for building a custom sponsorship.

    Steps:
    1. Select or create a sponsor
    2. Choose a base package
    3. Customize benefits
    4. Set terms (fee, dates, renewal, notes)
    5. Review and create
    """

    TOTAL_STEPS = 5

    def _get_step(self, request):
        """Return the current step number, clamped to valid range."""
        try:
            step = int(request.GET.get("step", 1))
        except (TypeError, ValueError):
            step = 1
        return max(1, min(step, self.TOTAL_STEPS))

    def _get_composer_data(self, request):
        """Return the composer session data dict."""
        return request.session.get("composer", {})

    def _set_composer_data(self, request, data):
        """Save composer data to session."""
        request.session["composer"] = data
        request.session.modified = True

    def _max_allowed_step(self, data):
        """Return the highest step the user can navigate to based on completed data."""
        if not data.get("sponsor_id") and not data.get("new_sponsor"):
            return 1
        if "package_id" not in data and "custom_package" not in data:
            return 2
        if "benefit_ids" not in data:
            return 3
        if "fee" not in data:
            return 4
        return 5

    def get(self, request):
        """Render the current wizard step."""
        # Clear session when starting a new composer session
        if request.GET.get("new") == "1":
            data = {}
            # Pre-select sponsor if passed
            sponsor_id = request.GET.get("sponsor_id")
            if sponsor_id:
                try:
                    sponsor = Sponsor.objects.get(pk=int(sponsor_id))
                    data["sponsor_id"] = sponsor.pk
                except (Sponsor.DoesNotExist, TypeError, ValueError):
                    pass
            self._set_composer_data(request, data)
            # Skip to step 2 if sponsor was pre-selected
            if data.get("sponsor_id"):
                return redirect(reverse("manage_composer") + "?step=2")
            return redirect(reverse("manage_composer"))

        step = self._get_step(request)
        data = self._get_composer_data(request)

        # Don't let user skip ahead
        max_step = self._max_allowed_step(data)
        step = min(step, max_step)

        handler = {
            1: self._render_step1,
            2: self._render_step2,
            3: self._render_step3,
            4: self._render_step4,
            5: self._render_step5,
        }[step]
        return handler(request, data)

    def post(self, request):
        """Process the current step's form data and advance."""
        step = self._get_step(request)
        handler = {
            1: self._process_step1,
            2: self._process_step2,
            3: self._process_step3,
            4: self._process_step4,
            5: self._process_step5,
        }[step]
        return handler(request)

    # ── Step 1: Select Sponsor ──

    def _render_step1(self, request, data):
        q = request.GET.get("q", "")
        sponsors = Sponsor.objects.order_by("name")
        if q:
            sponsors = sponsors.filter(Q(name__icontains=q))
        sponsors = sponsors[:50]
        form = ComposerSponsorForm()
        context = {
            "step": 1,
            "total_steps": self.TOTAL_STEPS,
            "data": data,
            "sponsors": sponsors,
            "search_query": q,
            "form": form,
        }
        return render(request, "sponsors/manage/composer.html", context)

    def _process_step1(self, request):
        data = self._get_composer_data(request)
        action = request.POST.get("action", "")

        if action == "select_sponsor":
            sponsor_id = request.POST.get("sponsor_id")
            if sponsor_id:
                sponsor = get_object_or_404(Sponsor, pk=sponsor_id)
                # Reset all data for fresh start with this sponsor
                data = {"sponsor_id": sponsor.pk}
                self._set_composer_data(request, data)
                return redirect(reverse("manage_composer") + "?step=2")

        elif action == "create_sponsor":
            form = ComposerSponsorForm(request.POST)
            if form.is_valid():
                sponsor = form.save(commit=False)
                sponsor.creator = request.user
                sponsor.save()
                data["sponsor_id"] = sponsor.pk
                data.pop("new_sponsor", None)
                self._set_composer_data(request, data)
                return redirect(reverse("manage_composer") + "?step=2")
            # Re-render with errors
            sponsors = Sponsor.objects.order_by("name")[:50]
            context = {
                "step": 1,
                "total_steps": self.TOTAL_STEPS,
                "data": data,
                "sponsors": sponsors,
                "search_query": "",
                "form": form,
            }
            return render(request, "sponsors/manage/composer.html", context)

        messages.error(request, "Please select or create a sponsor.")
        return redirect(reverse("manage_composer") + "?step=1")

    # ── Step 2: Choose Package ──

    def _get_composer_year(self, data):
        """Return the year to use for the composer, defaulting to current year."""
        if data.get("year"):
            return data["year"]
        try:
            return SponsorshipCurrentYear.get_year()
        except SponsorshipCurrentYear.DoesNotExist:
            return None

    def _render_step2(self, request, data):
        year = self._get_composer_year(data)
        if request.GET.get("year"):
            with contextlib.suppress(TypeError, ValueError):
                year = int(request.GET["year"])

        packages = SponsorshipPackage.objects.filter(year=year).order_by("-sponsorship_amount") if year else []
        years = sorted(
            set(SponsorshipPackage.objects.values_list("year", flat=True).distinct()) - {None},
            reverse=True,
        )
        context = {
            "step": 2,
            "total_steps": self.TOTAL_STEPS,
            "data": data,
            "packages": packages,
            "years": years,
            "selected_year": year,
        }
        return render(request, "sponsors/manage/composer.html", context)

    def _process_step2(self, request):
        data = self._get_composer_data(request)
        package_id = request.POST.get("package_id", "")
        year = request.POST.get("year", "")

        if year:
            with contextlib.suppress(TypeError, ValueError):
                data["year"] = int(year)

        if package_id == "custom":
            data["package_id"] = None
            data["custom_package"] = True
            data["benefit_ids"] = []
        elif package_id:
            try:
                pkg = SponsorshipPackage.objects.get(pk=int(package_id))
                data["package_id"] = pkg.pk
                data.pop("custom_package", None)
                # Pre-populate benefits from package
                data["benefit_ids"] = list(pkg.benefits.values_list("pk", flat=True))
                data["year"] = pkg.year
            except (SponsorshipPackage.DoesNotExist, ValueError):
                messages.error(request, "Invalid package selection.")
                self._set_composer_data(request, data)
                return redirect(reverse("manage_composer") + "?step=2")
        else:
            messages.error(request, "Please select a package.")
            self._set_composer_data(request, data)
            return redirect(reverse("manage_composer") + "?step=2")

        self._set_composer_data(request, data)
        return redirect(reverse("manage_composer") + "?step=3")

    # ── Step 3: Customize Benefits ──

    def _render_step3(self, request, data):
        year = self._get_composer_year(data)
        programs = SponsorshipProgram.objects.all().order_by("order")
        benefits_by_program = []
        for program in programs:
            benefits = SponsorshipBenefit.objects.filter(program=program, year=year).order_by("order")
            if benefits.exists():
                benefits_by_program.append({"program": program, "benefits": benefits})

        selected_ids = set(data.get("benefit_ids", []))
        selected_benefits = SponsorshipBenefit.objects.filter(pk__in=selected_ids).select_related("program")
        total_value = sum(b.internal_value or 0 for b in selected_benefits)

        # Determine which benefits come from the selected package (locked)
        package_benefit_ids = set()
        if data.get("package_id"):
            pkg = SponsorshipPackage.objects.filter(pk=data["package_id"]).first()
            if pkg:
                package_benefit_ids = set(pkg.benefits.values_list("pk", flat=True))

        context = {
            "step": 3,
            "total_steps": self.TOTAL_STEPS,
            "data": data,
            "benefits_by_program": benefits_by_program,
            "selected_benefits": selected_benefits,
            "selected_ids": selected_ids,
            "total_value": total_value,
            "package_benefit_ids": package_benefit_ids,
        }
        return render(request, "sponsors/manage/composer.html", context)

    def _process_step3(self, request):
        data = self._get_composer_data(request)
        benefit_ids_raw = request.POST.getlist("benefit_ids")
        benefit_ids = []
        for bid in benefit_ids_raw:
            try:
                benefit_ids.append(int(bid))
            except (TypeError, ValueError):
                continue
        data["benefit_ids"] = benefit_ids
        self._set_composer_data(request, data)
        return redirect(reverse("manage_composer") + "?step=4")

    # ── Step 4: Set Terms ──

    def _render_step4(self, request, data):
        initial = {}
        if data.get("fee") is not None:
            initial["fee"] = data["fee"]
        elif data.get("package_id"):
            try:
                pkg = SponsorshipPackage.objects.get(pk=data["package_id"])
                initial["fee"] = pkg.sponsorship_amount
            except SponsorshipPackage.DoesNotExist:
                pass
        if data.get("start_date"):
            initial["start_date"] = data["start_date"]
        if data.get("end_date"):
            initial["end_date"] = data["end_date"]
        if data.get("renewal") is not None:
            initial["renewal"] = data["renewal"]
        if data.get("notes"):
            initial["notes"] = data["notes"]

        form = ComposerTermsForm(initial=initial)

        # Calculate total internal value from selected benefits for staff reference
        total_internal_value = 0
        benefit_ids = data.get("benefit_ids", [])
        if benefit_ids:
            total_internal_value = (
                SponsorshipBenefit.objects.filter(pk__in=benefit_ids).aggregate(total=Sum("internal_value"))["total"]
                or 0
            )

        context = {
            "step": 4,
            "total_steps": self.TOTAL_STEPS,
            "data": data,
            "form": form,
            "total_internal_value": total_internal_value,
        }
        return render(request, "sponsors/manage/composer.html", context)

    def _process_step4(self, request):
        data = self._get_composer_data(request)
        form = ComposerTermsForm(request.POST)
        if form.is_valid():
            data["fee"] = form.cleaned_data["fee"]
            data["start_date"] = form.cleaned_data["start_date"].isoformat()
            data["end_date"] = form.cleaned_data["end_date"].isoformat()
            data["renewal"] = form.cleaned_data["renewal"]
            data["notes"] = form.cleaned_data["notes"]
            self._set_composer_data(request, data)
            return redirect(reverse("manage_composer") + "?step=5")
        # Re-render with errors
        context = {
            "step": 4,
            "total_steps": self.TOTAL_STEPS,
            "data": data,
            "form": form,
        }
        return render(request, "sponsors/manage/composer.html", context)

    # ── Step 5: Review & Create ──

    def _render_step5(self, request, data):
        sponsor = None
        if data.get("sponsor_id"):
            sponsor = Sponsor.objects.filter(pk=data["sponsor_id"]).first()

        package = None
        if data.get("package_id"):
            package = SponsorshipPackage.objects.filter(pk=data["package_id"]).first()

        selected_benefits = (
            SponsorshipBenefit.objects.filter(pk__in=data.get("benefit_ids", []))
            .select_related("program")
            .order_by("program__order", "order")
        )
        total_value = sum(b.internal_value or 0 for b in selected_benefits)

        # Group selected benefits by program for the review display
        programs_map = {}
        for b in selected_benefits:
            prog = b.program
            if prog.pk not in programs_map:
                programs_map[prog.pk] = {"program": prog, "benefits": []}
            programs_map[prog.pk]["benefits"].append(b)
        review_benefits_by_program = list(programs_map.values())

        # Determine which benefits come from the selected package
        package_benefit_ids = set()
        if data.get("package_id") and package:
            package_benefit_ids = set(package.benefits.values_list("pk", flat=True))

        context = {
            "step": 5,
            "total_steps": self.TOTAL_STEPS,
            "data": data,
            "sponsor": sponsor,
            "package": package,
            "selected_benefits": selected_benefits,
            "total_value": total_value,
            "review_benefits_by_program": review_benefits_by_program,
            "package_benefit_ids": package_benefit_ids,
        }
        return render(request, "sponsors/manage/composer.html", context)

    @transaction.atomic
    def _process_step5(self, request):
        data = self._get_composer_data(request)
        action = request.POST.get("action", "create")

        # Resolve sponsor
        sponsor = None
        if data.get("sponsor_id"):
            sponsor = Sponsor.objects.filter(pk=data["sponsor_id"]).first()
        if not sponsor:
            messages.error(request, "Sponsor not found. Please start over.")
            return redirect(reverse("manage_composer") + "?step=1")

        # Resolve benefits
        benefit_ids = data.get("benefit_ids", [])
        benefits = list(SponsorshipBenefit.objects.filter(pk__in=benefit_ids).select_related("program"))

        # Resolve package
        package = None
        if data.get("package_id"):
            package = SponsorshipPackage.objects.filter(pk=data["package_id"]).first()

        if action == "create":
            return self._handle_create(request, data, sponsor, package, benefits)
        if action == "send_internal":
            return self._handle_send_internal(request, data, sponsor, package, benefits)
        if action == "send_proposal":
            return self._handle_send_proposal(request, data, sponsor, package, benefits)
        messages.error(request, "Unknown action.")
        return redirect(reverse("manage_composer") + "?step=5")

    def _create_sponsorship(self, request, data, sponsor, package, benefits):
        """Create the Sponsorship and SponsorBenefit copies."""
        import datetime

        year = data.get("year") or SponsorshipCurrentYear.get_year()

        sponsorship = Sponsorship.objects.create(
            submited_by=request.user,
            sponsor=sponsor,
            level_name="" if not package else package.name,
            package=package,
            sponsorship_fee=data.get("fee"),
            for_modified_package=True,
            year=year,
            start_date=datetime.date.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            renewal=data.get("renewal", False),
        )

        for benefit in benefits:
            SponsorBenefit.new_copy(benefit, sponsorship=sponsorship)

        return sponsorship

    def _handle_create(self, request, data, sponsor, package, benefits):
        """Create the sponsorship and clear wizard state."""
        from apps.sponsors.exceptions import SponsorWithExistingApplicationError

        try:
            sponsorship = self._create_sponsorship(request, data, sponsor, package, benefits)
        except SponsorWithExistingApplicationError:
            messages.error(request, f"{sponsor.name} already has an in-progress sponsorship application.")
            return redirect(reverse("manage_composer") + "?step=5")

        # Clear wizard state
        request.session.pop("composer", None)
        messages.success(request, f"Sponsorship created for {sponsor.name}.")
        return redirect(reverse("manage_sponsorship_detail", args=[sponsorship.pk]))

    def _build_summary_text(self, data, sponsor, package, benefits):
        """Build a plain-text summary of the composed sponsorship."""
        lines = [
            f"Sponsorship Proposal for {sponsor.name}",
            "=" * 50,
            "",
            f"Sponsor: {sponsor.name}",
            f"Package: {package.name if package else 'Custom'}",
            f"Year: {data.get('year', 'N/A')}",
            f"Fee: ${data.get('fee', 0):,}",
            f"Start Date: {data.get('start_date', 'N/A')}",
            f"End Date: {data.get('end_date', 'N/A')}",
            f"Renewal: {'Yes' if data.get('renewal') else 'No'}",
            "",
            "Benefits:",
            "-" * 30,
        ]
        total = 0
        for b in benefits:
            val = b.internal_value or 0
            total += val
            lines.append(f"  - {b.program.name} > {b.name} (${val:,})")
        lines.append(f"\nTotal Internal Value: ${total:,}")
        if data.get("notes"):
            lines.extend(["", "Notes:", data["notes"]])
        return "\n".join(lines)

    def _handle_send_internal(self, request, data, sponsor, package, benefits):
        """Send a proposal summary to an internal email address."""
        from django.core.mail import EmailMessage

        email_addr = request.POST.get("internal_email", "").strip()
        if not email_addr:
            messages.error(request, "Please enter an email address for internal review.")
            return redirect(reverse("manage_composer") + "?step=5")

        body = self._build_summary_text(data, sponsor, package, benefits)
        email = EmailMessage(
            subject=f"[Internal Review] Sponsorship Proposal for {sponsor.name}",
            body=body,
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
            to=[email_addr],
        )
        email.send()
        messages.success(request, f"Proposal sent to {email_addr} for internal review.")
        return redirect(reverse("manage_composer") + "?step=5")

    def _handle_send_proposal(self, request, data, sponsor, package, benefits):
        """Send a proposal summary to sponsor contacts."""
        from django.core.mail import EmailMessage

        contacts = SponsorContact.objects.filter(sponsor=sponsor)
        emails = [c.email for c in contacts if c.email]
        if not emails:
            messages.error(request, "No contacts found for this sponsor.")
            return redirect(reverse("manage_composer") + "?step=5")

        body = self._build_summary_text(data, sponsor, package, benefits)
        email = EmailMessage(
            subject="Sponsorship Proposal from the Python Software Foundation",
            body=body,
            from_email=settings.SPONSORSHIP_NOTIFICATION_FROM_EMAIL,
            to=emails,
        )
        email.send()
        messages.success(request, f"Proposal sent to sponsor contacts ({', '.join(emails)}).")
        return redirect(reverse("manage_composer") + "?step=5")


class GuideView(SponsorshipAdminRequiredMixin, TemplateView):
    """Help guide for the sponsor management UI."""

    template_name = "sponsors/manage/guide.html"
