from django.contrib import admin

from app.cms.admin import NameSlugAdmin

from app.companies.models import Company


@admin.register(Company)
class CompanyAdmin(NameSlugAdmin):
    search_fields = ['name']
    list_display = ['__str__', 'contact', 'email']
    ordering = ['-pk']
