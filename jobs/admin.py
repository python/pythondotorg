from django.contrib import admin

from .models import JobType, JobCategory, Job
from cms.admin import NameSlugAdmin, ContentManageableModelAdmin


class JobAdmin(ContentManageableModelAdmin):
    date_hierarchy = 'created'
    filter_horizontal = ['job_types']
    list_display = ['__str__', 'job_title', 'status', 'company_name']
    list_filter = ['status', 'telecommuting']
    raw_id_fields = ['category']


admin.site.register(JobType, NameSlugAdmin)
admin.site.register(JobCategory, NameSlugAdmin)
admin.site.register(Job, JobAdmin)
