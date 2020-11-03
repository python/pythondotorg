from ordered_model.admin import OrderedModelAdmin

from django.urls import path, reverse
from django.contrib import admin
from django.utils.html import mark_safe
from django.shortcuts import get_object_or_404, render

from .models import (
    SponsorshipPackage,
    SponsorshipProgram,
    SponsorshipBenefit,
    Sponsor,
    Sponsorship,
)
from cms.admin import ContentManageableModelAdmin


@admin.register(SponsorshipProgram)
class SponsorshipProgramAdmin(OrderedModelAdmin):
    pass


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


@admin.register(Sponsor)
class SponsorAdmin(ContentManageableModelAdmin):
    pass


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = [
        "sponsor_info",
        "applied_on",
        "approved_on",
        "start_date",
        "end_date",
        "display_sponsorship_link",
    ]

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("sponsor_info")

    def display_sponsorship_link(self, obj):
        url = reverse("admin:sponsors_sponsorship_preview", args=[obj.pk])
        return mark_safe(f'<a href="{url}" target="_blank">Click to preview</a>')

    display_sponsorship_link.short_description = "Preview sponsorship"

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
