from django.contrib import admin

from cms.admin import NameSlugAdmin

from .models import Company


class CompanyAdmin(NameSlugAdmin):
    search_fields = ['name']
    list_display = ['__str__', 'contact', 'email']
    ordering = ['-pk']

admin.site.register(Company, CompanyAdmin)
