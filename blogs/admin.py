"""Admin configuration for the blogs app."""

from django.contrib import admin
from django.core.management import call_command

from .models import BlogEntry, Feed, FeedAggregate


@admin.register(BlogEntry)
class BlogEntryAdmin(admin.ModelAdmin):
    """Admin interface for blog entries imported from RSS feeds."""

    list_display = ["title", "pub_date"]
    date_hierarchy = "pub_date"
    actions = ["sync_new_entries"]

    @admin.action(description="Sync new blog entries")
    def sync_new_entries(self, request, queryset):
        """Trigger the update_blogs management command to sync new entries."""
        call_command("update_blogs")
        self.message_user(request, "Blog entries updated.")


@admin.register(FeedAggregate)
class FeedAggregateAdmin(admin.ModelAdmin):
    """Admin interface for managing feed aggregates."""

    list_display = ["name", "slug", "description"]
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Feed)
