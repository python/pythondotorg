# Create your views here.
import datetime

from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Event, EventCategory, EventLocation


class EventDetail(DetailView):
    model = Event

    def get_queryset(self):
        return super().get_queryset().select_related()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        dt = data['object'].next_time.dt_start
        data.update({
            'next_7': dt + datetime.timedelta(days=7),
            'next_30': dt + datetime.timedelta(days=30),
            'next_90': dt + datetime.timedelta(days=90),
            'next_365': dt + datetime.timedelta(days=365),
        })
        return data


class EventList(ListView):
    model = Event
    paginate_by = 6

    def get_object(self, queryset=None):
        return None

    def get_queryset(self):
        return Event.objects.for_datetime(timezone.now())

    def get_context_data(self, **kwargs):
        featured_events = self.get_queryset().filter(featured=True)
        try:
            kwargs['featured'] = featured_events[0]
        except IndexError:
            pass

        kwargs['event_categories'] = EventCategory.objects.all()[:10]
        kwargs['event_locations'] = EventLocation.objects.all()[:10]
        kwargs['object'] = self.get_object()

        return super().get_context_data(**kwargs)


class EventListByDate(EventList):

    def get_object(self):
        year = int(self.kwargs['year'])
        month = int(self.kwargs['month'])
        day = int(self.kwargs['day'])
        return datetime.date(year, month, day)

    def get_queryset(self):
        return Event.objects.for_datetime(self.get_object())


class EventListByCategory(EventList):
    def get_object(self, queryset=None):
        return EventCategory.objects.get(slug=self.kwargs['slug'])

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(categories__slug=self.kwargs['slug'])


class EventListByLocation(EventList):
    def get_object(self, queryset=None):
        return EventLocation.objects.get(pk=self.kwargs['pk'])

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(venue__pk=self.kwargs['pk'])


class EventCategoryList(ListView):
    model = EventCategory
    paginate_by = 30


class EventLocationList(ListView):
    model = EventLocation
    paginate_by = 30
