from rest_framework import serializers

from .models import Page


class PageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Page
        fields = (
            'title',
            'path',
            'keywords',
            'description',
            'content',
            'is_published',
            'template_name',
            'resource_uri',
        )
