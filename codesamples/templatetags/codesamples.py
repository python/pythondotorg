from django import template

from ..models import CodeSample

register = template.Library()


@register.simple_tag
def get_code_samples_latest(limit=5):
    """ Return last 5 published code samples """
    return CodeSample.objects.published()[:limit]
