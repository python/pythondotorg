"""Simple "flat pages".

These get used for the static (non-automated) large chunks of content. Notice
that pages don't have any actual notion of where they live; instead, they're
positioned into the URL structure using the nav app.
"""

import re
from copy import deepcopy

import cmarkgfm
from cmarkgfm.cmark import Options as cmarkgfmOptions
from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from markupfield.fields import MarkupField
from markupfield.markup import DEFAULT_MARKUP_TYPES

from cms.models import ContentManageable
from fastly.utils import purge_url

from .managers import PageQuerySet

DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")

PAGE_PATH_RE = re.compile(
    r"""
    ^
    /?                      # We can optionally start with a /
    ([a-z0-9-\.]+)            # Then at least one path segment...
    (/[a-z0-9-\.]+)*        # And then possibly more "/whatever" segments
    /?                      # Possibly ending with a slash
    $
    """,
    re.VERBOSE,
)

is_valid_page_path = validators.RegexValidator(
    regex=PAGE_PATH_RE,
    message=(
        'Please enter a valid URL segment, e.g. "foo" or "foo/bar". '
        "Only lowercase letters, numbers, hyphens and periods are allowed."
    ),
)

RENDERERS = deepcopy(DEFAULT_MARKUP_TYPES)
for i, renderer in enumerate(RENDERERS):
    if renderer[0] == "markdown":
        markdown_index = i

RENDERERS[markdown_index] = ("markdown", cmarkgfm.github_flavored_markdown_to_html, "Markdown")

# Add our own Github style Markdown parser, which doesn't apply the default
# tagfilter used by Github (we can be more liberal, since we know our page
# editors).


def unsafe_markdown_to_html(text, options=0):
    """Render the given GitHub-flavored Makrdown to HTML.

    This function is similar to cmarkgfm.github_flavored_markdown_to_html(),
    except that it allows raw HTML to get rendered, which is useful when
    using jQuery UI script extensions on pages.

    """
    # Set options for cmarkgfm for "unsafe" renderer, see
    # https://github.com/theacodes/cmarkgfm#advanced-usage
    options = options | (cmarkgfmOptions.CMARK_OPT_UNSAFE | cmarkgfmOptions.CMARK_OPT_GITHUB_PRE_LANG)
    return cmarkgfm.markdown_to_html_with_extensions(
        text, options=options, extensions=["table", "autolink", "strikethrough", "tasklist"]
    )


RENDERERS.append(
    (
        "markdown_unsafe",
        unsafe_markdown_to_html,
        "Markdown (unsafe)",
    )
)


class Page(ContentManageable):
    """A flat CMS page positioned into the URL structure via the nav app."""

    title = models.CharField(max_length=500)
    keywords = models.CharField(max_length=1000, blank=True, help_text="HTTP meta-keywords")
    description = models.TextField(blank=True, help_text="HTTP meta-description")
    path = models.CharField(max_length=500, validators=[is_valid_page_path], unique=True, db_index=True)
    content = MarkupField(markup_choices=RENDERERS, default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=True, db_index=True)
    content_type = models.CharField(max_length=150, default="text/html")
    template_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Example: 'pages/about.html'. If this isn't provided, the system will use 'pages/default.html'.",
    )

    objects = PageQuerySet.as_manager()

    class Meta:
        """Meta configuration for Page."""

        ordering = ["title", "path"]

    def clean(self):
        """Strip leading and trailing slashes from the page path."""
        self.path = self.path.strip("/")

    def get_title(self):
        """Return the page title, or a placeholder if none is set."""
        if self.title:
            return self.title
        return "** No Title **"

    def __str__(self):
        """Return the page title."""
        return self.title

    def get_absolute_url(self):
        """Return the absolute URL for this page."""
        return f"/{self.path}/"


@receiver(post_save, sender=Page)
def purge_fastly_cache(sender, instance, **kwargs):
    """Purge fastly.com cache if in production and the page is published.

    Requires settings.FASTLY_API_KEY being set.
    """
    purge_url(f"/{instance.path}")
    if not instance.path.endswith("/"):
        purge_url(f"/{instance.path}/")


def page_image_path(instance, filename):
    """Build the upload path for a page image using the parent page's path."""
    return f"{instance.page.path}/{filename}"


class Image(models.Model):
    """An image file attached to a CMS Page."""

    page = models.ForeignKey("pages.Page", on_delete=models.CASCADE)
    image = models.ImageField(upload_to=page_image_path, max_length=400)

    def __str__(self):
        """Return the image URL."""
        return self.image.url


class DocumentFile(models.Model):
    """A document file attached to a CMS Page."""

    page = models.ForeignKey("pages.Page", on_delete=models.CASCADE)
    document = models.FileField(upload_to="files/", max_length=500)

    def __str__(self):
        """Return the document URL."""
        return self.document.url
