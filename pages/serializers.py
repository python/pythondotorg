"""DRF serializers for the pages app."""

from rest_framework import serializers

from .models import Page


class PageSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the Page model in the REST API."""

    class Meta:
        """Meta configuration for PageSerializer."""

        model = Page
        fields = (
            "title",
            "path",
            "keywords",
            "description",
            "content",
            "is_published",
            "template_name",
            "resource_uri",
        )
