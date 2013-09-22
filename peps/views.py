from django.views.generic import TemplateView

from .models import Pep, PepCategory, PepStatus, PepOwner, PepType


class PepListView(TemplateView):
    """
    View to display the listing of PEPs
    """
    template_name = 'peps/list.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['categories'] = PepCategory.objects.select_related('peps').all()
        context['statuses'] = PepStatus.objects.all()
        context['types'] = PepType.objects.all()
        context['owners'] = PepOwner.objects.all()
        context['peps'] = Pep.objects.all().order_by('number')

        return context

