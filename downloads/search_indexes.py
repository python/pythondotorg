"""Haystack search indexes for the downloads app."""

import datetime

from django.template.defaultfilters import striptags, truncatewords_html
from django.utils import timezone
from haystack import indexes

from downloads.models import Release


class ReleaseIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for Python releases."""

    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    description = indexes.CharField()
    path = indexes.CharField()
    release_notes_url = indexes.CharField(model_attr="release_notes_url")
    release_date = indexes.DateTimeField(model_attr="release_date")

    include_template = indexes.CharField()

    def get_model(self):
        """Return the Release model class."""
        return Release

    def index_queryset(self, using=None):
        """Only index published Releases."""
        return self.get_model().objects.filter(is_published=True)

    def prepare_include_template(self, obj):
        """Return the search result template path."""
        return "search/includes/downloads.release.html"

    def prepare_path(self, obj):
        """Return the absolute URL for the release."""
        return obj.get_absolute_url()

    def prepare_version(self, obj):
        """Return the display version string."""
        return obj.get_version_display()

    def prepare_description(self, obj):
        """Return a truncated plain-text description."""
        return striptags(truncatewords_html(obj.content.rendered, 50))

    def prepare(self, obj):
        """Boost recent releases."""
        data = super().prepare(obj)

        now = timezone.now()
        three_months = now - datetime.timedelta(days=90)
        six_months = now - datetime.timedelta(days=180)
        two_years = now - datetime.timedelta(days=730)

        # Boost releases in the last 3 months and 6 months
        # reduce boost on releases older than 2 years
        if obj.release_date >= three_months:
            data["boost"] = 1.2
        elif obj.release_date >= six_months:
            data["boost"] = 1.1
        elif obj.release_date <= two_years:
            data["boost"] = 0.8

        return data
