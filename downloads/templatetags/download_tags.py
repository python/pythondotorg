from django import template

register = template.Library()


@register.filter
def strip_minor_version(version):
    return '.'.join(version.split('.')[:2])
