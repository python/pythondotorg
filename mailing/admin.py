from django.contrib import admin
from django.forms.models import modelform_factory

from mailing.forms import BaseEmailTemplateForm


class BaseEmailTemplateAdmin(admin.ModelAdmin):
    list_display = ["internal_name", "subject"]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["internal_name"]
    fieldsets = (
        (None, {
            'fields': ('internal_name',)
        }),
        ('Email template', {
            'fields': ('subject', 'content')
        }),
        ('Timtestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_form(self, *args, **kwargs):
        kwargs["form"] = modelform_factory(self.model, form=BaseEmailTemplateForm)
        return super().get_form(*args, **kwargs)
