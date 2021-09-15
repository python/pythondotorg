from django.contrib import admin

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
