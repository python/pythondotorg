from django.contrib import admin

from .models import OS, Release, ReleaseFile
from cms.admin import ContentManageableModelAdmin, ContentManageableStackedInline


class OSAdmin(ContentManageableModelAdmin):
    model = OS
    prepopulated_fields = {"slug": ("name",)}


class ReleaseFileInline(ContentManageableStackedInline):
    model = ReleaseFile
    extra = 0


class ReleaseAdmin(ContentManageableModelAdmin):
    inlines = [ReleaseFileInline]
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ['release_page']
    date_hierarchy = 'release_date'
    list_display = ['__str__', 'is_published', 'show_on_download_page']
    list_filter = ['version', 'is_published', 'show_on_download_page']
    search_fields = ['name', 'slug']

admin.site.register(OS, OSAdmin)
admin.site.register(Release, ReleaseAdmin)
