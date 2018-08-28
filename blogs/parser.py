import datetime
import feedparser

from django.template.loader import render_to_string
from django.utils.timezone import make_aware, utc

from boxes.models import Box
from .models import BlogEntry


def get_all_entries(feed_url):
    """ Retrieve all entries from a feed URL """
    d = feedparser.parse(feed_url)
    entries = []

    for e in d['entries']:
        published = make_aware(
            datetime.datetime(*e['published_parsed'][:7]), timezone=utc
        )

        entry = {
            'title': e['title'],
            'summary': e.get('summary', ''),
            'pub_date': published,
            'url': e['link'],
        }

        entries.append(entry)

    return entries


def _render_blog_supernav(entry):
    """ Utility to make testing update_blogs management command easier """
    return render_to_string('blogs/supernav.html', {'entry': entry})


def update_blog_supernav():
    """Retrieve latest entry and update blog supernav item """
    latest_entry = BlogEntry.objects.filter(feed_id=1).latest()
    rendered_box = _render_blog_supernav(latest_entry)

    box, _ = Box.objects.update_or_create(
        label='supernav-python-blog',
        defaults={
            'content': rendered_box,
            'content_markup_type': 'html',
        }
    )
