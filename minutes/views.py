from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.views.generic import DetailView, ListView

from .models import Minutes


class MinutesList(ListView):
    model = Minutes
    template_name = 'minutes/minutes_list.html'
    context_object_name = 'minutes_list'

    def get_queryset(self):
        if self.request.user.is_staff:
            qs = Minutes.objects.all()
        else:
            qs = Minutes.objects.published()

        return qs.order_by('-date')


class MinutesDetail(DetailView):
    model = Minutes
    template_name = 'minutes/minutes_detail.html'
    context_object_name = 'minutes'

    def get_object(self, queryset=None):
        # Allow site admins to see drafts
        if self.request.user.is_staff:
            qs = Minutes.objects.all()
        else:
            qs = Minutes.objects.published()

        try:
            obj = qs.get(
                date__year=int(self.kwargs['year']),
                date__month=int(self.kwargs['month']),
                date__day=int(self.kwargs['day']),
            )
        except ObjectDoesNotExist:
            raise Http404("Minutes does not exist")

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        same_year = Minutes.objects.filter(
            date__year=self.object.date.year,
        ).order_by('date')

        context['same_year_minutes'] = same_year

        return context
