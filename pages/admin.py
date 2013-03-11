from django.contrib import admin

from cms.admin import ContentManageableModelAdmin
from .models import Page


class PageAdmin(ContentManageableModelAdmin):
    search_fields = ['title', 'path']


admin.site.register(Page, PageAdmin)
