from django.contrib import admin

from cms.admin import ContentManageableModelAdmin

from .models import CodeSample

admin.site.register(CodeSample, ContentManageableModelAdmin)
