from django import template

from ..models import BlogEntry

register = template.Library()


@register.simple_tag
def get_latest_blog_entries(limit=5):
    """ Return limit of latest blog entries """
    return BlogEntry.objects.order_by("-pub_date")[:limit]


@register.simple_tag
def feed_list(slug, limit=10):
    """
    Returns a list of blog entries for the given FeedAggregate slug.

    {% feed_list 'psf' as entries %}
    {% for entry in entries %}
      {{ entry }}
    {% endfor %}
    """
    return BlogEntry.objects.filter(
        feed__feedaggregate__slug=slug).order_by('-pub_date')[:limit]

