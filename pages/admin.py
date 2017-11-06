from django.conf import settings
from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe

from bs4 import BeautifulSoup

from cms.admin import ContentManageableModelAdmin
from .models import Page, Image, DocumentFile


class PageAdminImageFileWidget(admin.widgets.AdminFileWidget):

    def render(self, name, value, attrs=None):
        """ Fix admin rendering """
        content = super().render(name, value, attrs=None)
        soup = BeautifulSoup(content, 'lxml')

        # Show useful link/relationship in admin
        a_href = soup.find('a')
        if a_href and a_href.attrs['href']:
            a_href.attrs['href'] = a_href.attrs['href'].replace(settings.MEDIA_ROOT, settings.MEDIA_URL)
            a_href.string = a_href.text.replace(settings.MEDIA_ROOT, settings.MEDIA_URL)

            if '//' in a_href.attrs['href']:
                a_href.attrs['href'] = a_href.attrs['href'].replace('//', '/')
                a_href.string = a_href.text.replace('//', '/')

        return mark_safe(soup)


class ImageInlineAdmin(admin.StackedInline):
    model = Image
    extra = 1

    formfield_overrides = {
        models.ImageField: {'widget': PageAdminImageFileWidget},
    }


class DocumentFileInlineAdmin(admin.StackedInline):
    model = DocumentFile
    extra = 1

    formfield_overrides = {
        models.FileField: {'widget': PageAdminImageFileWidget},
    }


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
    list_display = ('get_title', 'path', 'is_published',)
    list_filter = [PagePathFilter, 'is_published']
    inlines = [ImageInlineAdmin, DocumentFileInlineAdmin]
    fieldsets = [
        (None, {'fields': ('title', 'keywords', 'description', 'path', 'content', 'content_markup_type', 'is_published')}),
        ('Advanced options', {'classes': ('collapse',), 'fields': ('template_name',)}),
    ]
    save_as = True

admin.site.register(Page, PageAdmin)
