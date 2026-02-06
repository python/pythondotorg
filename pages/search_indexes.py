"""Haystack search indexes for the pages app."""

from django.template.defaultfilters import striptags, truncatewords_html
from haystack import indexes

from pages.models import Page


class PageIndex(indexes.SearchIndex, indexes.Indexable):
    """Search index for CMS pages, indexing title, description, and path."""

    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr="title")
    description = indexes.CharField(model_attr="description")
    path = indexes.CharField(model_attr="path")
    include_template = indexes.CharField()

    def get_model(self):
        """Return the Page model class."""
        return Page

    def prepare_include_template(self, obj):
        """Return the template path for rendering search result snippets."""
        return "search/includes/pages.page.html"

    def prepare_description(self, obj):
        """Create a description if none exists."""
        if obj.description:
            return obj.description
        return striptags(truncatewords_html(obj.content.rendered, 50))

    def index_queryset(self, using=None):
        """Only index published pages."""
        return self.get_model().objects.filter(is_published=True)
