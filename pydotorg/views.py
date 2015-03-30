from django.conf import settings
from django.views.generic.base import TemplateView

from codesamples.models import CodeSample


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'code_samples': CodeSample.objects.published()[:5],
            'blog_url': settings.PYTHON_BLOG_URL,
        })
        return context
