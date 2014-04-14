import logging
from django import template
from ..models import Box

log = logging.getLogger(__name__)
register = template.Library()

@register.simple_tag
def box(label):
    try:
        return Box.objects.only('content').get(label=label).content.rendered
    except Box.DoesNotExist:
        log.warning('WARNING: box not found: label=%s', label)
        return ''
