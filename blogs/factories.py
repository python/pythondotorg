from django.conf import settings

from .models import Feed


def initial_data():
    feed, _ = Feed.objects.get_or_create(
        id=1,
        defaults={
            'name': 'Python Insider',
            'website_url': settings.PYTHON_BLOG_URL,
            'feed_url': settings.PYTHON_BLOG_FEED_URL,
        }
    )
    return {
        'feeds': [feed],
    }
