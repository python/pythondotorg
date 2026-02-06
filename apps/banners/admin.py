"""Admin configuration for the banners app."""

from django.contrib import admin

from apps.banners.models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Admin interface for managing site-wide banners."""

    list_display = ("title", "active", "psf_pages_only")
