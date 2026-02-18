"""Admin configuration for the boxes app."""

from django.contrib import admin

from boxes.models import Box
from cms.admin import ContentManageableModelAdmin


@admin.register(Box)
class BoxAdmin(ContentManageableModelAdmin):
    """Admin interface for managing reusable content boxes."""

    ordering = ("label",)
