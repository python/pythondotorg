from django.contrib import admin
from django.forms.models import modelform_factory
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import get_object_or_404

from mailing.forms import BaseEmailTemplateForm


class BaseEmailTemplateAdmin(admin.ModelAdmin):
    change_form_template = "mailing/admin/base_email_template_form.html"
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
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def get_form(self, *args, **kwargs):
        kwargs["form"] = modelform_factory(self.model, form=BaseEmailTemplateForm)
        return super().get_form(*args, **kwargs)

    def get_urls(self):
        urls = super().get_urls()
        prefix = self.model._meta.db_table
        my_urls = [
            path(
                "<int:pk>/preview-content/",
                self.admin_site.admin_view(self.preview_email_template),
                name=f"{prefix}_preview",
            ),
        ]
        return my_urls + urls

    def preview_email_template(self, request, pk, *args, **kwargs):
        qs = self.get_queryset(request)
        template = get_object_or_404(qs, pk=pk)
        return HttpResponse(template.render_content({}))
