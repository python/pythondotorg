import itertools

from django.http import HttpResponse
from django.core import serializers
from django.conf import settings
from django.views.generic.base import TemplateView

from codesamples.models import CodeSample
import sitetree.models
import boxes.models
import feedbacks.models
import pages.models


class IndexView(TemplateView):
    template_name = "python/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['code_samples'] = CodeSample.objects.published()[:5]
        return context


def get_dev_fixture(request):
    response = HttpResponse(content_type='application/json')
    models = (sitetree.models.Tree, sitetree.models.TreeItem,
              boxes.models.Box, pages.models.Page,
              feedbacks.models.FeedbackCategory, feedbacks.models.IssueType)
    if settings.DEBUG:
        objects = itertools.chain.from_iterable(M.objects.all() for M in models)
    else:
        objects = []
    serializers.serialize('json', objects, stream=response)
    return response
