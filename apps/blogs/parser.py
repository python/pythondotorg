"""RSS feed parsing and blog supernav rendering utilities."""

import datetime
from urllib.parse import urlparse, urlunparse

import feedparser
from django.conf import settings
from django.template.loader import render_to_string

from apps.blogs.models import BlogEntry, Feed
from apps.boxes.models import Box

# Blogger serves RSS entry links with this legacy domain instead of
# the canonical blog.python.org hostname.
_BLOGGER_LEGACY_HOST = "pythoninsider.blogspot.com"


def _normalize_blog_url(url):
    """Rewrite legacy Blogger URLs to the canonical blog.python.org domain."""
    parsed = urlparse(url)
    if parsed.hostname == _BLOGGER_LEGACY_HOST:
        canonical = urlparse(settings.PYTHON_BLOG_URL)
        return urlunparse(parsed._replace(scheme=canonical.scheme, netloc=canonical.netloc))
    return url


def get_all_entries(feed_url):
    """Retrieve all entries from a feed URL."""
    d = feedparser.parse(feed_url)
    entries = []

    for e in d["entries"]:
        published = datetime.datetime(*e["published_parsed"][:7], tzinfo=datetime.UTC)

        entry = {
            "title": e["title"],
            "summary": e.get("summary", ""),
            "pub_date": published,
            "url": _normalize_blog_url(e["link"]),
        }

        entries.append(entry)

    return entries


def _render_blog_supernav(entry):
    """Render blog supernav for testing update_blogs management command."""
    return render_to_string("blogs/supernav.html", {"entry": entry})


def update_blog_supernav():
    """Retrieve latest entry and update blog supernav item."""
    try:
        latest_entry = BlogEntry.objects.filter(
            feed=Feed.objects.get(
                feed_url=settings.PYTHON_BLOG_FEED_URL,
            )
        ).latest()
    except (BlogEntry.DoesNotExist, Feed.DoesNotExist):
        pass
    else:
        rendered_box = _render_blog_supernav(latest_entry)
        box, created = Box.objects.update_or_create(
            label="supernav-python-blog",
            defaults={
                "content": rendered_box,
                "content_markup_type": "html",
            },
        )
        if not created:
            box.save()
