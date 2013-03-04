from django.contrib import admin

from .models import Story, StoryCategory
from cms.admin import ContentManageableModelAdmin, NameSlugAdmin


class StoryCategoryAdmin(NameSlugAdmin):
    prepopulated_fields = {'slug': ('name',)}


class StoryAdmin(ContentManageableModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['category']

    def get_list_filter(self, request):
        fields = list(super().get_list_filter(request))
        return fields + ['is_published']

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        return fields + ['is_published']


admin.site.register(StoryCategory, StoryCategoryAdmin)
admin.site.register(Story, StoryAdmin)
