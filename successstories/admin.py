from django.contrib import admin
from django.contrib import messages

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
        return fields + ['is_published', 'featured', 'get_weight_display']

    def save_model(self, request, obj, form, change):
        """ Alert user to weight inbalance situations """
        obj.save()
        weight_total = Story.objects.featured_weight_total()
        if weight_total != 100:
            messages.warning(request, "Warning, Success Story Featured Weights do not total 100%")


admin.site.register(StoryCategory, StoryCategoryAdmin)
admin.site.register(Story, StoryAdmin)
