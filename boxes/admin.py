from django.contrib import admin
from cms.admin import ContentManageableModelAdmin
from .models import Box


class BoxAdmin(ContentManageableModelAdmin):
    ordering = ('label', )


admin.site.register(Box, BoxAdmin)
