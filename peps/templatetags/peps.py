from django import template

from ..models import Pep

register = template.Library()


@register.assignment_tag
def get_latest_accepted_peps():
    """ Return last 4 Accepted PEPs """
    return Pep.objects.filter(
        status__name='Accepted proposal'
    ).order_by('-updated')[:4]
