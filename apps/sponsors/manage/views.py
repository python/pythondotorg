"""Views for the sponsor management UI.

Locked down to users in the 'Sponsorship Admin' group (or staff/superuser).
"""

import contextlib
import csv

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
    AddBenefitToSponsorshipForm,
    BenefitFilterForm,
    CloneYearForm,
    CurrentYearForm,
    ExecuteContractForm,
    NotificationTemplateForm,
    SendSponsorshipNotificationManageForm,
    SponsorContactForm,
    SponsorEditForm,
    SponsorshipApproveForm,
    SponsorshipBenefitManageForm,
    SponsorshipEditForm,
    SponsorshipFilterForm,
    SponsorshipPackageManageForm,
)
from apps.sponsors.models import (
    BenefitFeature,
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
        """Return context with related sponsorships and packages."""
        context = super().get_context_data(**kwargs)
        context["is_create"] = False
        related = self.object.related_sponsorships.select_related("sponsor", "package").order_by("-year", "status")
        context["related_sponsorships"] = related
        context["related_sponsorships_count"] = related.count()
        context["benefit_packages"] = self.object.packages.order_by("order")
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
