import itertools

from django.http import HttpResponse
from django.core import serializers
import sitetree.models

import boxes.models
import feedbacks.models
import pages.models

def get_dev_fixture(request):
    response = HttpResponse(content_type='application/json')
    models = (sitetree.models.Tree, sitetree.models.TreeItem,
              boxes.models.Box, pages.models.Page,
              feedbacks.models.FeedbackCategory, feedbacks.models.IssueType)
    objects = itertools.chain.from_iterable(M.objects.all() for M in models)
    serializers.serialize('json', objects, stream=response)
    return response
