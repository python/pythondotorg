"""Views for the sponsor management UI.

Locked down to users in the 'Sponsorship Admin' group (or staff/superuser).
"""

import contextlib

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
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
    SponsorEditForm,
    SponsorshipApproveForm,
    SponsorshipBenefitManageForm,
    SponsorshipEditForm,
    SponsorshipFilterForm,
    SponsorshipPackageManageForm,
)
from apps.sponsors.models import (
    Contract,
    Sponsor,
    SponsorBenefit,
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
    """Generate and send contract for signing."""

    def get(self, request, pk):
        """Render the contract send confirmation page."""
        sp = get_object_or_404(Sponsorship.objects.select_related("sponsor"), pk=pk)
        try:
            contract = sp.contract
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists for this sponsorship.")
            return redirect(reverse("manage_sponsorship_detail", args=[pk]))
        context = {"sponsorship": sp, "contract": contract}
        return render(request, "sponsors/manage/contract_send.html", context)

    def post(self, request, pk):
        """Generate and send the contract."""
        sp = get_object_or_404(Sponsorship, pk=pk)
        try:
            contract = sp.contract
            use_case = use_cases.SendContractUseCase.build()
            use_case.execute(contract, request=request)
            messages.success(request, "Contract generated and sent.")
        except Contract.DoesNotExist:
            messages.error(request, "No contract exists.")
        except InvalidStatusError as e:
            messages.error(request, str(e))
        return redirect(reverse("manage_sponsorship_detail", args=[pk]))


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
