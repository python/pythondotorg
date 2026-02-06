"""Views for listing and displaying PSF meeting minutes."""

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.views.generic import DetailView, ListView

from .models import Minutes


class MinutesList(ListView):
    """List view of all meeting minutes, ordered by date descending."""

    model = Minutes
    template_name = "minutes/minutes_list.html"
    context_object_name = "minutes_list"

    def get_queryset(self):
        """Return all minutes for staff, published minutes for everyone else."""
        qs = Minutes.objects.all() if self.request.user.is_staff else Minutes.objects.published()

        return qs.order_by("-date")


class MinutesDetail(DetailView):
    """Detail view for a single set of meeting minutes identified by date."""

    model = Minutes
    template_name = "minutes/minutes_detail.html"
    context_object_name = "minutes"

    def get_object(self, queryset=None):
        """Look up minutes by year, month, and day URL parameters."""
        # Allow site admins to see drafts
        qs = Minutes.objects.all() if self.request.user.is_staff else Minutes.objects.published()

        try:
            obj = qs.get(
                date__year=int(self.kwargs["year"]),
                date__month=int(self.kwargs["month"]),
                date__day=int(self.kwargs["day"]),
            )
        except ObjectDoesNotExist as e:
            msg = "Minutes does not exist"
            raise Http404(msg) from e

        return obj

    def get_context_data(self, **kwargs):
        """Add other minutes from the same year to the context."""
        context = super().get_context_data(**kwargs)

        same_year = Minutes.objects.filter(
            date__year=self.object.date.year,
        ).order_by("date")

        context["same_year_minutes"] = same_year

        return context
