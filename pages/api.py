from rest_framework.authentication import TokenAuthentication

from pydotorg.resources import GenericResource, OnlyPublishedAuthorization
from pydotorg.drf import (
    BaseReadOnlyAPIViewSet, BaseFilterSet, IsStaffOrReadOnly,
)

from .models import Page
from .serializers import PageSerializer


class PageResource(GenericResource):
    class Meta(GenericResource.Meta):
        authorization = OnlyPublishedAuthorization()
        queryset = Page.objects.all()
        resource_name = 'pages/page'
        fields = [
            'creator', 'last_modified_by',
            'title', 'keywords', 'description',
            'path', 'content', 'is_published',
            'template_name'

        ]
        filtering = {
            'title': ('exact',),
            'keywords': ('exact', 'icontains'),
            'path': ('exact',),
            'is_published': ('exact',),
        }


class PageFilterSet(BaseFilterSet):

    class Meta:
        model = Page
        fields = {
            'title': ['exact'],
            'path': ['exact'],
            'keywords': ['exact', 'icontains'],
            'is_published': ['exact'],
        }


class PageViewSet(BaseReadOnlyAPIViewSet):
    model = Page
    serializer_class = PageSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filter_class = PageFilterSet
