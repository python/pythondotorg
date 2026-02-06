"""Admin configuration for the companies app."""

from django.contrib import admin

from cms.admin import NameSlugAdmin

from .models import Company


@admin.register(Company)
class CompanyAdmin(NameSlugAdmin):
    """Admin interface for managing company profiles."""

    search_fields = ["name"]
    list_display = ["__str__", "contact", "email"]
    ordering = ["-pk"]
