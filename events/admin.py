from django.contrib import admin
from cms.admin import ContentManageableModelAdmin, NameSlugAdmin

from .models import Calendar, EventCategory, Event, OccurringRule, RecurringRule, Alarm, EventLocation


class EventInline(admin.StackedInline):
    model = Event
    extra = 0


class OccurringRuleInline(admin.StackedInline):
    model = OccurringRule
    extra = 0
    max_num = 1


class RecurringRuleInline(admin.StackedInline):
    model = RecurringRule
    extra = 0


class AlarmInline(admin.StackedInline):
    model = Alarm
    extra = 0


@admin.register(Event)
class EventAdmin(ContentManageableModelAdmin):
    inlines = [OccurringRuleInline, RecurringRuleInline]
    list_display = ['__str__', 'calendar', 'featured']
    list_filter = ['calendar', 'featured']
    raw_id_fields = ['venue']
    search_fields = ['title']


@admin.register(EventLocation)
class EventLocationAdmin(admin.ModelAdmin):
    list_filter = ['calendar']


admin.site.register(EventCategory, NameSlugAdmin)
admin.site.register((OccurringRule, RecurringRule))
admin.site.register((Alarm, Calendar), ContentManageableModelAdmin)
