"""Factory functions for creating blog test and seed data."""

from django.conf import settings

from apps.blogs.models import Feed


def initial_data():
    """Create and return the default Python Insider blog feed."""
    feed, _ = Feed.objects.get_or_create(
        id=1,
        defaults={
            "name": "Python Insider",
            "website_url": settings.PYTHON_BLOG_URL,
            "feed_url": settings.PYTHON_BLOG_FEED_URL,
        },
    )
    return {
        "feeds": [feed],
    }
