from django import template
from django.utils.dateformat import format

register = template.Library()


@register.inclusion_tag('cms/iso_time_tag.html')
def iso_time_tag(date):
    return {
        'timestamp': format(date, 'c'),
        'month': format(date, 'm'),
        'day': format(date, 'd'),
        'year': format(date, 'Y'),
    }
