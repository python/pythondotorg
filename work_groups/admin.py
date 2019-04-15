from django.contrib import admin

from cms.admin import ContentManageableModelAdmin

from .models import WorkGroup


@admin.register(WorkGroup)
class WorkGroupAdmin(ContentManageableModelAdmin):
    search_fields = ['name', 'slug', 'url', 'short_description', 'purpose']
    list_display = ('name', 'active', 'approved')
    list_filter = ('active', 'approved')
    fieldsets = [
        (None, {'fields': (
            'name',
            'slug',
            'active',
            'approved',
            'url',
            'short_description',
            'purpose',
            'purpose_markup_type',
            'active_time',
            'active_time_markup_type',
            'core_values',
            'core_values_markup_type',
            'rules',
            'rules_markup_type',
            'communication',
            'communication_markup_type',
            'support',
            'support_markup_type',
            'organizers',
            'members',
        )})
    ]
