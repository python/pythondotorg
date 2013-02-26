from django.contrib import admin

from cms.admin import NameSlugAdmin

from .models import Company


admin.site.register(Company, NameSlugAdmin)
