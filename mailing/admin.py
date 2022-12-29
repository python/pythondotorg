from django.contrib import admin
from django.forms.models import modelform_factory
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from mailing.forms import BaseEmailTemplateForm


def archive_selected_email_templates(modeladmin, request, queryset):
    queryset.update(active=False)
archive_selected_email_templates.short_description = "Archive selected Sponsor Email notification templates"


class EmailTemplateIsActiveListFilter(admin.SimpleListFilter):
    title = _('Active')

    parameter_name = 'active'

    def lookups(self, request, model_admin):
        return (
            ('all', _('All')),
            (None, _('Yes')),
            ('no', _('No')),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'no':
            return queryset.filter(active=False)
        elif self.value() is None:
            return queryset.filter(active=True)
        return queryset


class BaseEmailTemplateAdmin(admin.ModelAdmin):
    change_form_template = "mailing/admin/base_email_template_form.html"
    list_display = ["internal_name", "subject", "active"]
    list_filter = [EmailTemplateIsActiveListFilter]
    readonly_fields = ["created_at", "updated_at"]
    search_fields = ["internal_name"]
    actions = [archive_selected_email_templates]
    fieldsets = (
        (None, {
            'fields': ('internal_name',)
        }),
        ('Email template', {
            'fields': ('subject', 'content')
        }),
        (None, {
            'fields': ('active',)
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
