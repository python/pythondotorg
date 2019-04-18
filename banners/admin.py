from django.contrib import admin

from banners.models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "active", "psf_pages_only")
