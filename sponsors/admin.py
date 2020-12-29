from ordered_model.admin import OrderedModelAdmin

from django.contrib import messages
from django.urls import path, reverse
from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.html import mark_safe
from django.shortcuts import get_object_or_404, render, redirect

from .models import (
    SponsorshipPackage,
    SponsorshipProgram,
    SponsorshipBenefit,
    Sponsor,
    Sponsorship,
    SponsorContact,
    SponsorBenefit,
    LegalClause,
)
from sponsors import use_cases
from sponsors.forms import SponsorshipReviewAdminForm, SponsorBenefitAdminInlineForm
from sponsors.exceptions import SponsorshipInvalidStatusException
from cms.admin import ContentManageableModelAdmin


@admin.register(SponsorshipProgram)
class SponsorshipProgramAdmin(OrderedModelAdmin):
    ordering = ("order",)
    list_display = [
        "name",
        "move_up_down_links",
    ]


@admin.register(SponsorshipBenefit)
class SponsorshipBenefitAdmin(OrderedModelAdmin):
    ordering = ("program", "order")
    list_display = [
        "program",
        "short_name",
        "package_only",
        "internal_value",
        "move_up_down_links",
    ]
    list_filter = ["program", "package_only"]
    search_fields = ["name"]

    fieldsets = [
        (
            "Public",
            {
                "fields": (
                    "name",
                    "description",
                    "program",
                    "packages",
                    "package_only",
                    "new",
                ),
            },
        ),
        (
            "Internal",
            {
                "fields": (
                    "internal_description",
                    "internal_value",
                    "capacity",
                    "soft_capacity",
                    "legal_clauses",
                    "conflicts",
                )
            },
        ),
    ]


@admin.register(SponsorshipPackage)
class SponsorshipPackageAdmin(OrderedModelAdmin):
    ordering = ("order",)
    list_display = ["name", "move_up_down_links"]


class SponsorContactInline(admin.TabularInline):
    model = SponsorContact
    raw_id_fields = ["user"]
    extra = 0


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    inlines = [SponsorContactInline]


class SponsorBenefitInline(admin.TabularInline):
    model = SponsorBenefit
    form = SponsorBenefitAdminInlineForm
    fields = ["sponsorship_benefit", "benefit_internal_value"]
    extra = 0

    def has_add_permission(self, request):
        # this work around is necessary because the `obj` parameter was added to
        # InlineModelAdmin.has_add_permission only in Django 2.1.x and we're using 2.0.x
        has_add_permission = super().has_add_permission(request)
        match = request.resolver_match
        if match.url_name == "sponsors_sponsorship_change":
            sponsorship = self.parent_model.objects.get(pk=match.kwargs["object_id"])
            has_add_permission = has_add_permission and sponsorship.open_for_editing
        return has_add_permission

    def get_readonly_fields(self, request, obj=None):
        if obj and not obj.open_for_editing:
            return ["sponsorship_benefit", "benefit_internal_value"]
        return []

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        return obj.open_for_editing


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    change_form_template = "sponsors/admin/sponsorship_change_form.html"
    form = SponsorshipReviewAdminForm
    inlines = [SponsorBenefitInline]
    list_display = [
        "sponsor",
        "status",
        "applied_on",
        "approved_on",
        "start_date",
        "end_date",
        "display_sponsorship_link",
    ]
    list_filter = ["status"]
    readonly_fields = [
        "for_modified_package",
        "sponsor",
        "status",
        "applied_on",
        "rejected_on",
        "approved_on",
        "finalized_on",
        "get_estimated_cost",
        "get_sponsor_name",
        "get_sponsor_description",
        "get_sponsor_landing_page_url",
        "get_sponsor_web_logo",
        "get_sponsor_print_logo",
        "get_sponsor_primary_phone",
        "get_sponsor_mailing_address",
        "get_sponsor_contacts",
    ]

    fieldsets = [
        (
            "Sponsorship Data",
            {
                "fields": (
                    "sponsor",
                    "status",
                    "for_modified_package",
                    "level_name",
                    "sponsorship_fee",
                    "get_estimated_cost",
                    "start_date",
                    "end_date",
                ),
            },
        ),
        (
            "Sponsor Detailed Information",
            {
                "fields": (
                    "get_sponsor_name",
                    "get_sponsor_description",
                    "get_sponsor_landing_page_url",
                    "get_sponsor_web_logo",
                    "get_sponsor_print_logo",
                    "get_sponsor_primary_phone",
                    "get_sponsor_mailing_address",
                    "get_sponsor_contacts",
                ),
            },
        ),
        (
            "Events dates",
            {
                "fields": (
                    "applied_on",
                    "approved_on",
                    "rejected_on",
                    "finalized_on",
                ),
                "classes": ["collapse"],
            },
        ),
    ]

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsor")

    def display_sponsorship_link(self, obj):
        url = reverse("admin:sponsors_sponsorship_preview", args=[obj.pk])
        return mark_safe(f'<a href="{url}" target="_blank">Click to preview</a>')

    display_sponsorship_link.short_description = "Preview sponsorship"

    def get_estimated_cost(self, obj):
        cost = None
        html = "This sponsorship has not customizations so there's no estimated cost"
        if obj.for_modified_package:
            msg = "This sponsorship has customizations and this cost is a sum of all benefit's internal values from when this sponsorship was created"
            cost = intcomma(obj.estimated_cost)
            html = f"{cost} USD <br/><b>Important: </b> {msg}"
        return mark_safe(html)

    get_estimated_cost.short_description = "Estimated cost"

    def preview_sponsorship_view(self, request, pk):
        sponsorship = get_object_or_404(self.get_queryset(request), pk=pk)
        ctx = {"sponsorship": sponsorship}
        return render(request, "sponsors/admin/preview-sponsorship.html", context=ctx)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "<int:pk>/preview",
                self.admin_site.admin_view(self.preview_sponsorship_view),
                name="sponsors_sponsorship_preview",
            ),
            path(
                "<int:pk>/reject",
                # TODO: maybe it would be better to create a specific
                # group or permission to review sponsorship applications
                self.admin_site.admin_view(self.reject_sponsorship_view),
                name="sponsors_sponsorship_reject",
            ),
            path(
                "<int:pk>/approve",
                self.admin_site.admin_view(self.approve_sponsorship_view),
                name="sponsors_sponsorship_approve",
            ),
            path(
                "<int:pk>/enable-edit",
                self.admin_site.admin_view(self.rollback_to_editing_view),
                name="sponsors_sponsorship_rollback_to_edit",
            ),
        ]
        return my_urls + urls

    def get_sponsor_name(self, obj):
        return obj.sponsor.name

    get_sponsor_name.short_description = "Name"

    def get_sponsor_description(self, obj):
        return obj.sponsor.description

    get_sponsor_description.short_description = "Description"

    def get_sponsor_landing_page_url(self, obj):
        return obj.sponsor.landing_page_url

    get_sponsor_landing_page_url.short_description = "Landing Page URL"

    def get_sponsor_web_logo(self, obj):
        html = f"<img src='{obj.sponsor.web_logo.url}'/>"
        return mark_safe(html)

    get_sponsor_web_logo.short_description = "Web Logo"

    def get_sponsor_print_logo(self, obj):
        img = obj.sponsor.print_logo
        html = ""
        if img:
            html = f"<img src='{img.url}'/>"
        return mark_safe(html) if html else "---"

    get_sponsor_print_logo.short_description = "Print Logo"

    def get_sponsor_primary_phone(self, obj):
        return obj.sponsor.primary_phone

    get_sponsor_primary_phone.short_description = "Primary Phone"

    def get_sponsor_mailing_address(self, obj):
        sponsor = obj.sponsor
        city_row = (
            f"{sponsor.city} - {sponsor.get_country_display()} ({sponsor.country})"
        )
        if sponsor.state:
            city_row = f"{sponsor.city} - {sponsor.state} - {sponsor.get_country_display()} ({sponsor.country})"

        mail_row = sponsor.mailing_address_line_1
        if sponsor.mailing_address_line_2:
            mail_row += f" - {sponsor.mailing_address_line_2}"

        html = f"<p>{city_row}</p>"
        html += f"<p>{mail_row}</p>"
        html += f"<p>{sponsor.postal_code}</p>"
        return mark_safe(html)

    get_sponsor_mailing_address.short_description = "Mailing/Billing Address"

    def get_sponsor_contacts(self, obj):
        html = ""
        contacts = obj.sponsor.contacts.all()
        primary = [c for c in contacts if c.primary]
        not_primary = [c for c in contacts if not c.primary]
        if primary:
            html = "<b>Primary contacts</b><ul>"
            html += "".join(
                [f"<li>{c.name}: {c.email} / {c.phone}</li>" for c in primary]
            )
            html += "</ul>"
        if not_primary:
            html += "<b>Other contacts</b><ul>"
            html += "".join(
                [f"<li>{c.name}: {c.email} / {c.phone}</li>" for c in not_primary]
            )
            html += "</ul>"
        return mark_safe(html)

    get_sponsor_contacts.short_description = "Contacts"

    def rollback_to_editing_view(self, request, pk):
        sponsorship = get_object_or_404(self.get_queryset(request), pk=pk)

        if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
            try:
                sponsorship.rollback_to_editing()
                sponsorship.save()
                self.message_user(
                    request, "Sponsorship is now editable!", messages.SUCCESS
                )
            except SponsorshipInvalidStatusException as e:
                self.message_user(request, str(e), messages.ERROR)

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

    def reject_sponsorship_view(self, request, pk):
        sponsorship = get_object_or_404(self.get_queryset(request), pk=pk)

        if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
            try:
                use_case = use_cases.RejectSponsorshipApplicationUseCase.build()
                use_case.execute(sponsorship)
                self.message_user(
                    request, "Sponsorship was rejected!", messages.SUCCESS
                )
            except SponsorshipInvalidStatusException as e:
                self.message_user(request, str(e), messages.ERROR)

            redirect_url = reverse(
                "admin:sponsors_sponsorship_change", args=[sponsorship.pk]
            )
            return redirect(redirect_url)

        context = {"sponsorship": sponsorship}
        return render(
            request, "sponsors/admin/reject_application.html", context=context
        )

    def approve_sponsorship_view(self, request, pk):
        sponsorship = get_object_or_404(self.get_queryset(request), pk=pk)

        if request.method.upper() == "POST" and request.POST.get("confirm") == "yes":
            try:
                sponsorship.approve()
                sponsorship.save()
                self.message_user(
                    request, "Sponsorship was approved!", messages.SUCCESS
                )
            except SponsorshipInvalidStatusException as e:
                self.message_user(request, str(e), messages.ERROR)

            redirect_url = reverse(
                "admin:sponsors_sponsorship_change", args=[sponsorship.pk]
            )
            return redirect(redirect_url)

        context = {"sponsorship": sponsorship}
        return render(
            request, "sponsors/admin/approve_application.html", context=context
        )


@admin.register(LegalClause)
class LegalClauseModelAdmin(OrderedModelAdmin):
    list_display = ["internal_name"]
