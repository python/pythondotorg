"""Admin configuration for the codesamples app."""

from django.contrib import admin

from cms.admin import ContentManageableModelAdmin
from codesamples.models import CodeSample

admin.site.register(CodeSample, ContentManageableModelAdmin)
