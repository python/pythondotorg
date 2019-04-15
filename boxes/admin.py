from django.contrib import admin
from cms.admin import ContentManageableModelAdmin
from .models import Box


@admin.register(Box)
class BoxAdmin(ContentManageableModelAdmin):
    ordering = ('label', )
