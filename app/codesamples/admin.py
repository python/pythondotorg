from django.contrib import admin

from app.codesamples.models import CodeSample
from app.cms.admin import ContentManageableModelAdmin


admin.site.register(CodeSample, ContentManageableModelAdmin)
