from django.contrib import admin

from .models import JobType, JobCategory, Job
from cms.admin import NameSlugAdmin, ContentManageableModelAdmin


class JobAdmin(ContentManageableModelAdmin):
    date_hierarchy = 'created'
    filter_horizontal = ['job_types']
    list_display = ['__str__', 'job_title', 'status', 'company_name']
    list_filter = ['status', 'telecommuting']
    raw_id_fields = ['category']


class JobTypeAdmin(NameSlugAdmin):
    list_display = ['__str__', 'active']
    list_filter = ['active']
    ordering = ('-active', 'name')

admin.site.register(JobType, JobTypeAdmin)


class JobCategoryAdmin(NameSlugAdmin):
    list_display = ['__str__', 'active']
    list_filter = ['active']
    ordering = ('-active', 'name')

admin.site.register(JobCategory, JobCategoryAdmin)

admin.site.register(Job, JobAdmin)
