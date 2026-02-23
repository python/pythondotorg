"""Admin configuration for the downloads app."""

from django.contrib import admin

from apps.cms.admin import ContentManageableModelAdmin, ContentManageableStackedInline
from apps.downloads.models import (
    OS,
    Release,
    ReleaseFile,
    update_download_landing_sources_box,
    update_homepage_download_box,
    update_supernav,
)
from fastly.utils import purge_url


@admin.register(OS)
class OSAdmin(ContentManageableModelAdmin):
    """Admin interface for operating system entries."""

    model = OS
    prepopulated_fields = {"slug": ("name",)}


class ReleaseFileInline(ContentManageableStackedInline):
    """Inline admin for release files within a release."""

    model = ReleaseFile
    extra = 0


@admin.register(Release)
class ReleaseAdmin(ContentManageableModelAdmin):
    """Admin interface for Python releases."""

    inlines = [ReleaseFileInline]
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ["release_page"]
    date_hierarchy = "release_date"
    list_display = ["__str__", "is_published", "show_on_download_page"]
    list_filter = ["version", "is_published", "show_on_download_page"]
    search_fields = ["name", "slug"]
    ordering = ["-release_date"]

    def save_related(self, request, form, formsets, change):
        """Update supernav after inline ReleaseFiles are saved and purge CDN."""
        super().save_related(request, form, formsets, change)
        instance = form.instance
        if instance.is_published:
            update_supernav()
            update_download_landing_sources_box()
            update_homepage_download_box()
            purge_url("/box/supernav-python-downloads/")
            purge_url("/box/homepage-downloads/")
            purge_url("/box/download-sources/")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Add placeholder text to the release name field."""
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "name":
            field.widget.attrs["placeholder"] = "Python 3.X.YaN"
        return field

    class Media:
        """Media configuration for ReleaseAdmin."""

        js = ["js/admin/releaseAdmin.js"]
