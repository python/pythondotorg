"""Admin configuration for the success stories app."""

from django.contrib import admin
from django.utils.html import format_html

from cms.admin import ContentManageableModelAdmin, NameSlugAdmin
from successstories.models import Story, StoryCategory


@admin.register(StoryCategory)
class StoryCategoryAdmin(NameSlugAdmin):
    """Admin interface for story category management."""

    prepopulated_fields = {"slug": ("name",)}


@admin.register(Story)
class StoryAdmin(ContentManageableModelAdmin):
    """Admin interface for success story management."""

    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ["category", "submitted_by"]
    search_fields = ["name"]

    def get_list_filter(self, request):
        """Add is_published to the default list filters."""
        fields = list(super().get_list_filter(request))
        return [*fields, "is_published"]

    def get_list_display(self, request):
        """Add link, publication status, and featured flag to list display."""
        fields = list(super().get_list_display(request))
        return [*fields, "show_link", "is_published", "featured"]

    @admin.display(description="View on site")
    def show_link(self, obj):
        """Return a clickable link icon to the story's public page."""
        return format_html(f'<a href="{obj.get_absolute_url()}">\U0001f517</a>')
