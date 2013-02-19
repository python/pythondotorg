from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import Box

def box(request, label):
    b = get_object_or_404(Box, label=label)
    return HttpResponse(b.content.rendered)
