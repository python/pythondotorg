from django.contrib import admin
from django.core.management import call_command
from django.utils.html import format_html

from cms.admin import ContentManageableModelAdmin

from .models import BlogEntry, Contributor, Translation, Feed, FeedAggregate


class TranslationAdmin(ContentManageableModelAdmin):
    list_display = ['name', '_display_url']

    def _display_url(self, obj):
        return format_html('<a href="{0}">{0}</a>'.format(obj.url))

admin.site.register(Translation, TranslationAdmin)


class ContributorAdmin(ContentManageableModelAdmin):
    list_display = ['_display_name']

    def _display_name(self, obj):
        if obj.user.first_name or obj.user.last_name:
            return "{} {}".format(obj.user.first_name, obj.user.last_name)
        else:
            return "{} (PK#{})".format(obj.user.username, obj.user.pk)

admin.site.register(Contributor, ContributorAdmin)


class BlogEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'pub_date']
    date_hierarchy = 'pub_date'
    actions = ['sync_new_entries']

    def sync_new_entries(self, request, queryset):
        call_command('update_blogs')
        self.message_user(request, "Blog entries updated.")

    sync_new_entries.short_description = "Sync new blog entries"
    

admin.site.register(BlogEntry, BlogEntryAdmin)

class FeedAggregateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(FeedAggregate, FeedAggregateAdmin)

admin.site.register(Feed)
