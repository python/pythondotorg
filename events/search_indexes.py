from django.template.defaultfilters import truncatewords_html, striptags

from haystack import indexes

from .models import Event, Calendar


class CalendarIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(null=True)
    path = indexes.CharField()
    rss = indexes.CharField(model_attr='rss', null=True)
    twitter = indexes.CharField(model_attr='twitter', null=True)
    ical_url = indexes.CharField(model_attr='url', null=True)
    include_template = indexes.CharField()

    def get_model(self):
        return Calendar

    def prepare_path(self, obj):
        return obj.get_absolute_url()

    def prepare_description(self, obj):
        return striptags(truncatewords_html(obj.description, 50))

    def prepare_include_template(self, obj):
        return "search/includes/events.calendar.html"

    def prepare(self, obj):
        data = super().prepare(obj)
        data['boost'] = 4
        return data


class EventIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='title')
    description = indexes.CharField(null=True)
    venue = indexes.CharField(null=True)
    path = indexes.CharField()
    include_template = indexes.CharField()

    def get_model(self):
        return Event

    def prepare_include_template(self, obj):
        return "search/includes/events.event.html"

    def prepare_path(self, obj):
        return obj.get_absolute_url()

    def prepare_description(self, obj):
        return striptags(truncatewords_html(obj.description.rendered, 50))

    def prepare_venue(self, obj):
        if obj.venue:
            return obj.venue.name
        else:
            return None

    def prepare(self, obj):
        """ Boost events """
        data = super().prepare(obj)

        # Reduce boost of past events
        if obj.is_past:
            data['boost'] = 0.9
        elif obj.featured:
            data['boost'] = 1.2
        else:
            data['boost'] = 1.1

        return data
