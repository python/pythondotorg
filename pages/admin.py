from django.contrib import admin
from cms.admin import ContentManageableModelAdmin
from .models import Page

class PageAdmin(ContentManageableModelAdmin):
    pass

admin.site.register(Page, PageAdmin)
