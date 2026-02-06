from django.contrib import admin

from cms.admin import ContentManageableModelAdmin, ContentManageableStackedInline

from .models import OS, Release, ReleaseFile


@admin.register(OS)
class OSAdmin(ContentManageableModelAdmin):
    model = OS
    prepopulated_fields = {"slug": ("name",)}


class ReleaseFileInline(ContentManageableStackedInline):
    model = ReleaseFile
    extra = 0


@admin.register(Release)
class ReleaseAdmin(ContentManageableModelAdmin):
    inlines = [ReleaseFileInline]
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ["release_page"]
    date_hierarchy = "release_date"
    list_display = ["__str__", "is_published", "show_on_download_page"]
    list_filter = ["version", "is_published", "show_on_download_page"]
    search_fields = ["name", "slug"]
    ordering = ["-release_date"]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "name":
            field.widget.attrs["placeholder"] = "Python 3.X.YaN"
        return field

    class Media:
        js = ["js/admin/releaseAdmin.js"]
