"""Admin configuration for the work_groups app."""

from django.contrib import admin

from apps.cms.admin import ContentManageableModelAdmin
from apps.work_groups.models import WorkGroup


@admin.register(WorkGroup)
class WorkGroupAdmin(ContentManageableModelAdmin):
    """Admin interface for managing PSF working groups."""

    search_fields = ["name", "slug", "url", "short_description", "purpose"]
    list_display = ("name", "active", "approved")
    list_filter = ("active", "approved")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "active",
                    "approved",
                    "url",
                    "short_description",
                    "purpose",
                    "purpose_markup_type",
                    "active_time",
                    "active_time_markup_type",
                    "core_values",
                    "core_values_markup_type",
                    "rules",
                    "rules_markup_type",
                    "communication",
                    "communication_markup_type",
                    "support",
                    "support_markup_type",
                    "organizers",
                    "members",
                )
            },
        )
    ]
