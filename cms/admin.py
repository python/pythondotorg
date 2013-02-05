from django.contrib import admin

class ContentManageableModelAdmin(admin.ModelAdmin):
    """
    Base ModelAdmin class for any model that uses ContentManageable.
    """

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        return fields + ['created', 'updated', 'creator']

    def get_list_filter(self, request):
        fields = list(super().get_list_filter(request))
        return fields + ['created', 'updated']

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        return fields + ['created', 'updated']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creator = request.user
        return super().save_model(request, obj, form, change)
