from django.contrib import admin

from .models import Feedback, FeedbackCategory, IssueType
from cms.admin import NameSlugAdmin


class FeedbackAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    filter_horizontal = ['feedback_categories']
    list_display = ['pk', 'name', 'issue_type', 'is_beta_tester', 'created']
    list_filter = ['issue_type', 'feedback_categories', 'is_beta_tester']


admin.site.register(Feedback, FeedbackAdmin)
admin.site.register(FeedbackCategory, NameSlugAdmin)
admin.site.register(IssueType, NameSlugAdmin)
