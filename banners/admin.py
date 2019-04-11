from django.contrib import admin

from banners.models import Banner


class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "active", "psf_pages_only")

admin.site.register(Banner, BannerAdmin)
