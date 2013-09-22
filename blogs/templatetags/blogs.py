from django import template

from ..models import BlogEntry

register = template.Library()


@register.assignment_tag
def get_latest_blog_entries(number=5):
    """ Return number of latest blog entries """
    return BlogEntry.objects.order_by("-pub_date")[:number]
