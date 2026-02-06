"""Template filters for the nominations app."""

import random

from django import template

register = template.Library()


@register.filter
def shuffle(arg):
    """Return a shuffled copy of the given iterable."""
    aux = list(arg)[:]
    random.shuffle(aux)
    return aux
