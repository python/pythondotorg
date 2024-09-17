from django.contrib import admin
from app.cms.admin import ContentManageableModelAdmin
from app.boxes.models import Box


@admin.register(Box)
class BoxAdmin(ContentManageableModelAdmin):
    ordering = ('label', )
