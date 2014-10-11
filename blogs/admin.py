from django.contrib import admin

from cms.admin import ContentManageableModelAdmin

from .models import BlogEntry, Contributor, Translation


class TranslationAdmin(ContentManageableModelAdmin):
    list_display = ['name', '_display_url']

    def _display_url(self, obj):
        return """<a href="{0}">{0}</a>""".format(obj.url)

    _display_url.allow_tags = True

admin.site.register(Translation, TranslationAdmin)


class ContributorAdmin(ContentManageableModelAdmin):
    list_display = ['_display_name']

    def _display_name(self, obj):
        if obj.user.first_name or obj.user.last_name:
            return "{} {}".format(obj.user.first_name, obj.user.last_name)
        else:
            return "{} (PK#{})".format(obj.user.username, obj.user.pk)

admin.site.register(Contributor, ContributorAdmin)


class BlogEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'pub_date']
    date_hierarchy = 'pub_date'

admin.site.register(BlogEntry, BlogEntryAdmin)
