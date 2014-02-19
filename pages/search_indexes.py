from django.template.defaultfilters import truncatewords_html, striptags

from haystack import indexes

from .models import Page


class PageIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    path = indexes.CharField(model_attr='path')

    def get_model(self):
        return Page

    def prepare_description(self, obj):
        """ Create a description if none exists """
        if obj.description:
            return obj.description
        else:
            return striptags(truncatewords_html(obj.content, 50))
