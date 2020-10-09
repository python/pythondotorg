from django.contrib import admin

from .models import Minutes, Meeting, ConcernRole, Concern, ConcernedParty, DEFAULT_MARKUP_TYPE
from cms.admin import ContentManageableModelAdmin


@admin.register(Minutes)
class MinutesAdmin(ContentManageableModelAdmin):
    date_hierarchy = 'date'

    def get_list_filter(self, request):
        fields = list(super().get_list_filter(request))
        return fields + ['is_published']

    def get_list_display(self, request):
        fields = list(super().get_list_display(request))
        return fields + ['is_published']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ["title", "date"]


class ConcernRoleInline(admin.TabularInline):
    classes = ["collapse"]
    model = ConcernRole
    extra = 1


@admin.register(Concern)
class ConcernAdmin(admin.ModelAdmin):
    inlines = [ConcernRoleInline]


@admin.register(ConcernedParty)
class ConcernedPartyAdmin(admin.ModelAdmin):
    pass
