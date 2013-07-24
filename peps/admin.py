from django.contrib import admin

from .models import Pep, PepType, PepStatus, PepOwner, PepCategory
from cms.admin import ContentManageableModelAdmin


class PepAdmin(ContentManageableModelAdmin):
    list_display = ['title', 'type', 'status', 'category']
    list_filter = ['type', 'status', 'category']

admin.site.register(Pep, PepAdmin)

admin.site.register(PepType, ContentManageableModelAdmin)
admin.site.register(PepStatus, ContentManageableModelAdmin)
admin.site.register(PepOwner, ContentManageableModelAdmin)
admin.site.register(PepCategory, ContentManageableModelAdmin)
