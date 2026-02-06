"""Admin configuration for the events app."""

from django.contrib import admin

from cms.admin import ContentManageableModelAdmin, NameSlugAdmin
from events.models import Alarm, Calendar, Event, EventCategory, EventLocation, OccurringRule, RecurringRule


class EventInline(admin.StackedInline):
    """Inline admin for events within a calendar."""

    model = Event
    extra = 0


class OccurringRuleInline(admin.StackedInline):
    """Inline admin for single-occurrence rules within an event."""

    model = OccurringRule
    extra = 0
    max_num = 1


class RecurringRuleInline(admin.StackedInline):
    """Inline admin for recurring rules within an event."""

    model = RecurringRule
    extra = 0


class AlarmInline(admin.StackedInline):
    """Inline admin for alarms within an event."""

    model = Alarm
    extra = 0


@admin.register(Event)
class EventAdmin(ContentManageableModelAdmin):
    """Admin interface for events."""

    inlines = [OccurringRuleInline, RecurringRuleInline]
    list_display = ["__str__", "calendar", "featured"]
    list_filter = ["calendar", "featured"]
    raw_id_fields = ["venue"]
    search_fields = ["title"]


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    """Admin interface for event locations."""

    list_filter = ["calendar"]


admin.site.register(EventCategory, NameSlugAdmin)
admin.site.register((OccurringRule, RecurringRule))
admin.site.register((Alarm, Calendar), ContentManageableModelAdmin)
