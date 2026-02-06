"""Admin configuration for the companies app."""

from django.contrib import admin

from apps.cms.admin import NameSlugAdmin
from apps.companies.models import Company


@admin.register(Company)
class CompanyAdmin(NameSlugAdmin):
    """Admin interface for managing company profiles."""

    search_fields = ["name"]
    list_display = ["__str__", "contact", "email"]
    ordering = ["-pk"]
