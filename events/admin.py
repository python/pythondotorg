from django.contrib import admin
from cms.admin import ContentManageableModelAdmin

from .models import Calendar, EventCategory, Event, OccurringRule, RecurringRule, Alarm, EventLocation


class EventInline(admin.StackedInline):
    model = Event
    extra = 0


class CalendarAdmin(ContentManageableModelAdmin):
    inlines = [EventInline]


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


class EventAdmin(ContentManageableModelAdmin):
    inlines = [OccurringRuleInline, RecurringRuleInline, AlarmInline]
    list_display = ['__str__', 'calendar', 'featured']
    list_filter = ['calendar', 'featured']

admin.site.register(Calendar, CalendarAdmin)
admin.site.register(EventCategory, ContentManageableModelAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(OccurringRule)
admin.site.register(RecurringRule)
admin.site.register(Alarm, ContentManageableModelAdmin)
admin.site.register(EventLocation)
