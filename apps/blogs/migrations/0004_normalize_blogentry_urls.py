"""Rewrite legacy pythoninsider.blogspot.com URLs to blog.python.org.

Blogger's RSS feed historically served entry links under the old
pythoninsider.blogspot.com domain.  This one-time migration normalizes
existing BlogEntry rows so that the parser's runtime normalization
(added in the same changeset) doesn't create duplicates via
update_or_create.
"""

from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace


def normalize_blogentry_urls(apps, schema_editor):
    BlogEntry = apps.get_model("blogs", "BlogEntry")
    BlogEntry.objects.filter(url__contains="pythoninsider.blogspot.com").update(
        url=Replace("url", Value("pythoninsider.blogspot.com"), Value("blog.python.org")),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("blogs", "0003_alter_relatedblog_creator_and_more"),
    ]

    operations = [
        migrations.RunPython(
            normalize_blogentry_urls,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
