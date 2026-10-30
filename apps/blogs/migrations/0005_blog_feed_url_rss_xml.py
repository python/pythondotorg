"""Point the Python Insider feed at https://blog.python.org/rss.xml.

Python Insider moved from Blogger to GitHub Pages. The legacy Blogger
feed path ``feeds/posts/default?alt=rss`` is still served as a
compatibility copy, but it has no file extension so GitHub Pages sends
it as ``application/octet-stream``, which makes Safari and other
browsers download it instead of opening a feed reader. The blog's
canonical feed is ``/rss.xml``, served as ``application/xml``.

``update_blog_supernav`` looks up the Feed row by matching
``settings.PYTHON_BLOG_FEED_URL`` exactly, so the stored Feed row has to
change together with the setting. The ``blogs-subscriptions`` sidebar
box links to the feed too, so rewrite both its raw and rendered content.
"""

from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace

OLD_FEED_URL = "https://blog.python.org/feeds/posts/default?alt=rss"
NEW_FEED_URL = "https://blog.python.org/rss.xml"


def _replace_feed_url(apps, old, new):
    Feed = apps.get_model("blogs", "Feed")
    Feed.objects.filter(feed_url=old).update(feed_url=new)

    Box = apps.get_model("boxes", "Box")
    Box.objects.filter(label="blogs-subscriptions", content__contains=old).update(
        content=Replace("content", Value(old), Value(new)),
        _content_rendered=Replace("_content_rendered", Value(old), Value(new)),
    )


def forwards(apps, schema_editor):
    _replace_feed_url(apps, OLD_FEED_URL, NEW_FEED_URL)


def backwards(apps, schema_editor):
    _replace_feed_url(apps, NEW_FEED_URL, OLD_FEED_URL)


class Migration(migrations.Migration):
    dependencies = [
        ("blogs", "0004_normalize_blogentry_urls"),
        ("boxes", "0004_alter_box_creator_alter_box_last_modified_by"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
