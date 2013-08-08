"""
Simple "flat pages".

These get used for the static (non-automated) large chunks of content. Notice
that pages don't have any actual notion of where they live; instead, they're
positioned into the URL structure using the nav app.
"""

import re
from django.conf import settings
from django.core import validators
from django.db import models
from markupfield.fields import MarkupField
from cms.models import ContentManageable
from .managers import PageManager

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')

PAGE_PATH_RE = re.compile(r"""
    ^
    /?                      # We can optionally start with a /
    ([a-z0-9-]+)            # Then at least one path segment...
    (/[a-z0-9-]+)*          # And then possibly more "/whatever" segments
    /?                      # Possibly ending with a slash
    $
    """,
    re.X
)

is_valid_page_path = validators.RegexValidator(
    regex = PAGE_PATH_RE,
    message = ('Please enter a valid URL segment, e.g. "foo" or "foo/bar". '
               'Only lowercase letters, numbers, and hyphens are allowed.'),
)

class Page(ContentManageable):
    title = models.CharField(max_length=500)
    path = models.CharField(max_length=500, validators=[is_valid_page_path], unique=True, db_index=True)
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=True, db_index=True)
    template_name = models.CharField(max_length=100, blank=True,
        help_text="Example: 'pages/about.html'. If this isn't provided, the system will use 'pages/default.html'.")

    objects = PageManager()

    class Meta(object):
        ordering = ['title', 'path']

    def clean(self):
        # Strip leading and trailing slashes off self.path.
        self.path = self.path.strip('/')

    def __str__(self):
        return self.title
