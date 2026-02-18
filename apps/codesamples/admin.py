"""Admin configuration for the codesamples app."""

from django.contrib import admin

from apps.cms.admin import ContentManageableModelAdmin
from apps.codesamples.models import CodeSample

admin.site.register(CodeSample, ContentManageableModelAdmin)
