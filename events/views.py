import datetime

from django.contrib import messages
from django.core.mail import BadHeaderError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, ListView, FormView

from pydotorg.mixins import LoginRequiredMixin

from .models import Calendar, Event, EventCategory, EventLocation
from .forms import EventForm


class CalendarList(ListView):
    model = Calendar


class EventListBase(ListView):
    model = Event
    paginate_by = 6

    def get_object(self, queryset=None):
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        featured_events = self.get_queryset().filter(featured=True)
        try:
            context['featured'] = featured_events[0]
        except IndexError:
            pass

        context['event_categories'] = EventCategory.objects.all()[:10]
        context['event_locations'] = EventLocation.objects.all()[:10]
        context['object'] = self.get_object()
        return context


class EventHomepage(ListView):
    """ Main Event Landing Page """
    template_name = 'events/event_list.html'

    def get_queryset(self):
        return Event.objects.for_datetime(timezone.now()).order_by('occurring_rule__dt_start')


class EventDetail(DetailView):
    model = Event

    def get_queryset(self):
        return super().get_queryset().select_related()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if data['object'].next_time:
            dt = data['object'].next_time.dt_start
            data.update({
                'next_7': dt + datetime.timedelta(days=7),
                'next_30': dt + datetime.timedelta(days=30),
                'next_90': dt + datetime.timedelta(days=90),
                'next_365': dt + datetime.timedelta(days=365),
            })
        return data


class EventList(EventListBase):

    def get_queryset(self):
        return Event.objects.for_datetime(timezone.now()).filter(calendar__slug=self.kwargs['calendar_slug']).order_by('occurring_rule__dt_start')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events_today'] = Event.objects.until_datetime(timezone.now()).filter(calendar__slug=self.kwargs['calendar_slug'])[:2]
        context['calendar'] = get_object_or_404(Calendar, slug=self.kwargs['calendar_slug'])
        return context


class PastEventList(EventList):
    template_name = 'events/event_list_past.html'

    def get_queryset(self):
        return Event.objects.until_datetime(timezone.now()).filter(calendar__slug=self.kwargs['calendar_slug'])


class EventListByDate(EventList):
    def get_object(self):
        year = int(self.kwargs['year'])
        month = int(self.kwargs['month'])
        day = int(self.kwargs['day'])
        return datetime.date(year, month, day)

    def get_queryset(self):
        return Event.objects.for_datetime(self.get_object()).filter(calendar__slug=self.kwargs['calendar_slug'])


class EventListByCategory(EventList):
    def get_object(self, queryset=None):
        return get_object_or_404(EventCategory, calendar__slug=self.kwargs['calendar_slug'], slug=self.kwargs['slug'])

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(categories__slug=self.kwargs['slug'])


class EventListByLocation(EventList):
    def get_object(self, queryset=None):
        return get_object_or_404(EventLocation, calendar__slug=self.kwargs['calendar_slug'], pk=self.kwargs['pk'])

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(venue__pk=self.kwargs['pk'])


class EventCategoryList(ListView):
    model = EventCategory
    paginate_by = 30

    def get_queryset(self):
        return self.model.objects.filter(calendar__slug=self.kwargs['calendar_slug'])

    def get_context_data(self, **kwargs):
        kwargs['event_categories'] = self.get_queryset()[:10]

        return super().get_context_data(**kwargs)


class EventLocationList(ListView):
    model = EventLocation
    paginate_by = 30

    def get_queryset(self):
        return self.model.objects.filter(calendar__slug=self.kwargs['calendar_slug'])


class EventSubmit(LoginRequiredMixin, FormView):
    template_name = 'events/event_form.html'
    form_class = EventForm
    success_url = reverse_lazy('events:event_thanks')

    def form_valid(self, form):
        try:
            form.send_email(self.request.user)
        except BadHeaderError:
            messages.add_message(self.request, messages.ERROR, 'Invalid header found.')
            return redirect('events:event_submit')
        return super().form_valid(form)
