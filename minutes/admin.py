from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import mark_safe
from django.urls import path, reverse

from .models import Minutes, Meeting, ConcernRole, Concern, ConcernedParty, DEFAULT_MARKUP_TYPE, AgendaItem, MinuteItem
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


class AgendaItemInline(admin.TabularInline):
    model = AgendaItem
    readonly_fields = ['owners']
    extra = 0


class MinuteItemInline(admin.TabularInline):
    model = MinuteItem
    extra = 0
    classes = ["collapse"]


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "display_preview_minutes_link"]
    inlines = [AgendaItemInline, MinuteItemInline]

    def display_preview_minutes_link(self, obj):
        url = reverse("admin:preview_minutes_meeting", args=[obj.pk])
        return mark_safe(f'<a href="{url}" target="_blank">Click to preview</a>')
    display_preview_minutes_link.short_description = "Preview meeting minutes"

    def preview_minutes(self, request, meeting_pk):
        meeting = get_object_or_404(self.get_queryset(request), pk=meeting_pk)
        meeting.update_minutes()
        return redirect(meeting.minutes.get_absolute_url())

    def get_urls(self, *args, **kwargs):
        urls = super().get_urls(*args, **kwargs)
        custom_urls = [
            path("<int:meeting_pk>/view-minutes", self.admin_site.admin_view(self.preview_minutes), name="preview_minutes_meeting",),
        ]
        return custom_urls + urls


class ConcernRoleInline(admin.TabularInline):
    classes = ["collapse"]
    model = ConcernRole
    extra = 1


@admin.register(Concern)
class ConcernAdmin(admin.ModelAdmin):
    inlines = [ConcernRoleInline]
    list_display = ["__str__", "concern_roles"]

    def concern_roles(self, obj):
        return " / ".join(obj.concernrole_set.values_list("name", flat=True))
    concern_roles.description = "Roles"



@admin.register(ConcernedParty)
class ConcernedPartyAdmin(admin.ModelAdmin):
    list_display = ["__str__", "user", "role"]
    list_filter = ["role__concern"]
    raw_id_fields = ["user"]

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.select_related("user", "role__concern__parent_concern")
