import logging

from django import template
from django.utils.html import mark_safe

from ..models import Box

log = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def box(label):
    try:
        return mark_safe(Box.objects.only('content').get(label=label).content.rendered)
    except Box.DoesNotExist:
        log.warning('WARNING: box not found: label=%s', label)
        return ''
