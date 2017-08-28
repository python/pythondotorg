from rest_framework.authentication import TokenAuthentication

from pydotorg.drf import (
    BaseReadOnlyAPIViewSet, BaseFilterSet, IsStaffOrReadOnly,
)

from .models import Page
from .serializers import PageSerializer


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
