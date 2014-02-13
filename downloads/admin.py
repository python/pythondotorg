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

admin.site.register(OS, OSAdmin)
admin.site.register(Release, ReleaseAdmin)
