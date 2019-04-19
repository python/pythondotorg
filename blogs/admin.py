from django.contrib import admin
from django.core.management import call_command

from .models import BlogEntry, Feed, FeedAggregate


@admin.register(BlogEntry)
class BlogEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'pub_date']
    date_hierarchy = 'pub_date'
    actions = ['sync_new_entries']

    def sync_new_entries(self, request, queryset):
        call_command('update_blogs')
        self.message_user(request, "Blog entries updated.")

    sync_new_entries.short_description = "Sync new blog entries"


@admin.register(FeedAggregate)
class FeedAggregateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Feed)
