from django.views.generic.base import TemplateView

from codesamples.models import CodeSample


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'code_samples': CodeSample.objects.published()[:5],
        })
        return context
