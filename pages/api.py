"""REST API resources and viewsets for the pages app."""

from rest_framework.authentication import TokenAuthentication

from pages.models import Page
from pages.serializers import PageSerializer
from pydotorg.drf import (
    BaseFilterSet,
    BaseReadOnlyAPIViewSet,
    IsStaffOrReadOnly,
)
from pydotorg.resources import GenericResource, OnlyPublishedAuthorization


class PageResource(GenericResource):
    """Tastypie API resource for CMS pages."""

    class Meta(GenericResource.Meta):
        """Meta configuration for PageResource."""

        authorization = OnlyPublishedAuthorization()
        queryset = Page.objects.all()
        resource_name = "pages/page"
        fields = [
            "creator",
            "last_modified_by",
            "title",
            "keywords",
            "description",
            "path",
            "content",
            "is_published",
            "template_name",
        ]
        filtering = {
            "title": ("exact",),
            "keywords": ("exact", "icontains"),
            "path": ("exact",),
            "is_published": ("exact",),
        }
        abstract = False


class PageFilterSet(BaseFilterSet):
    """Filter set for querying pages by title, path, keywords, and status."""

    class Meta:
        """Meta configuration for PageFilterSet."""

        model = Page
        fields = {
            "title": ["exact"],
            "path": ["exact"],
            "keywords": ["exact", "icontains"],
            "is_published": ["exact"],
        }


class PageViewSet(BaseReadOnlyAPIViewSet):
    """Read-only DRF viewset for CMS pages."""

    model = Page
    serializer_class = PageSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filterset_class = PageFilterSet
