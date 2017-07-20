from django.contrib import admin

from cms.admin import NameSlugAdmin

from .models import Company


class CompanyAdmin(NameSlugAdmin):
    search_fields = ['name']

admin.site.register(Company, CompanyAdmin)
