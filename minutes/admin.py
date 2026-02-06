"""Admin configuration for the minutes app."""

from django.contrib import admin

from cms.admin import ContentManageableModelAdmin

from .models import Minutes


@admin.register(Minutes)
class MinutesAdmin(ContentManageableModelAdmin):
    """Admin interface for PSF meeting minutes management."""

    date_hierarchy = "date"

    def get_list_filter(self, request):
        """Add is_published to the default list filters."""
        fields = list(super().get_list_filter(request))
        return [*fields, "is_published"]

    def get_list_display(self, request):
        """Add is_published to the default list display columns."""
        fields = list(super().get_list_display(request))
        return [*fields, "is_published"]
