from django.views.generic import ListView

from .models import Sponsor


class SponsorList(ListView):
    model = Sponsor
    template_name = 'sponsors/sponsor_list.html'
    context_object_name = 'sponsors'

    def get_queryset(self):
        return Sponsor.objects.select_related().published()
