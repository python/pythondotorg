from django.contrib import admin

from .models import CodeSample
from cms.admin import ContentManageableModelAdmin


admin.site.register(CodeSample, ContentManageableModelAdmin)
