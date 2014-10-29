from django.template.defaultfilters import truncatewords_html, striptags

from haystack import indexes

from .models import Page


class PageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    path = indexes.CharField(model_attr='path')
    include_template = indexes.CharField()

    def get_model(self):
        return Page

    def prepare_include_template(self, obj):
        return "search/includes/pages.page.html"

    def prepare_description(self, obj):
        """ Create a description if none exists """
        if obj.description:
            return obj.description
        else:
            return striptags(truncatewords_html(obj.content.rendered, 50))

    def index_queryset(self, using=None):
        """ Only index published pages """
        return self.get_model().objects.filter(is_published=True)
