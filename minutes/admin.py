from django.contrib import admin

from cms.admin import ContentManageableModelAdmin

from .models import Minutes


@admin.register(Minutes)
class MinutesAdmin(ContentManageableModelAdmin):
    date_hierarchy = "date"

    def get_list_filter(self, request):
        fields = list(super().get_list_filter(request))
        return fields + ["is_published"]

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        return fields + ["is_published"]
