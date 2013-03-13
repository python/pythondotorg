from django.contrib import admin

from cms.admin import ContentManageableModelAdmin
from .models import Page


class PageAdmin(ContentManageableModelAdmin):
    search_fields = ['title', 'path']
    fieldsets = [
        (None, {'fields': ('title', 'path', 'content', 'content_markup_type', 'is_published')}),
        ('Advanced options', {'classes': ('collapse',), 'fields': ('template_name',)}),
    ]


admin.site.register(Page, PageAdmin)
