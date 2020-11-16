from ordered_model.admin import OrderedModelAdmin

from django.urls import path, reverse
from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.html import mark_safe
from django.shortcuts import get_object_or_404, render

from .models import (
    SponsorshipPackage,
    SponsorshipProgram,
    SponsorshipBenefit,
    Sponsor,
    Sponsorship,
    SponsorContact,
)
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
    list_filter = ["program"]
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
    extra = 0


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    inlines = [SponsorContactInline]


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = [
        "sponsor",
        "applied_on",
        "approved_on",
        "start_date",
        "end_date",
        "display_sponsorship_link",
    ]
    readonly_fields = [
        "for_modified_package",
        "sponsor",
        "status",
        "applied_on",
        "rejected_on",
        "get_estimated_cost",
        "approved_on",
        "finalized_on",
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
        msg = "This sponsorship has not customizations so there's no estimated cost"
        html = f"<b>Important: </b> {msg}"
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

    def get_urls(self, *args, **kwargs):
        urls = super().get_urls(*args, **kwargs)
        custom_urls = [
            path(
                "<int:pk>/preview",
                self.admin_site.admin_view(self.preview_sponsorship_view),
                name="sponsors_sponsorship_preview",
            ),
        ]
        return custom_urls + urls
