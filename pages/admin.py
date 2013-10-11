from django.contrib import admin

from cms.admin import ContentManageableModelAdmin
from .models import Page


class PagePathFilter(admin.SimpleListFilter):
    """ Admin list filter to allow drilling down by first two levels of pages """
    title = 'Path'
    parameter_name = 'pathlimiter'

    def lookups(self, request, model_admin):
        """ Determine the lookups we want to use """
        path_values = Page.objects.order_by('path').values_list('path', flat=True)
        path_set = []

        for v in path_values:
            if v == '':
                path_set.append(('', '/'))
            else:
                parts = v.split('/')[:2]
                new_value = "/".join(parts)
                new_tuple = (new_value, new_value)
                if new_tuple not in path_set:
                    path_set.append((new_value, new_value))

        return path_set

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(path__startswith=self.value())


class PageAdmin(ContentManageableModelAdmin):
    search_fields = ['title', 'path']
    list_display = ('get_title', 'path')
    list_filter = [PagePathFilter]
    fieldsets = [
        (None, {'fields': ('title', 'keywords', 'description', 'path', 'content', 'content_markup_type', 'is_published')}),
        ('Advanced options', {'classes': ('collapse',), 'fields': ('template_name',)}),
    ]


admin.site.register(Page, PageAdmin)
