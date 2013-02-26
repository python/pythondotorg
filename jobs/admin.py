from django.contrib import admin

from cms.admin import NameSlugAdmin, ContentManageableModelAdmin

from .models import JobType, JobCategory, Job, Company


admin.site.register(JobType, NameSlugAdmin)
admin.site.register(JobCategory, NameSlugAdmin)
admin.site.register(Company, NameSlugAdmin)
admin.site.register(Job, ContentManageableModelAdmin)
