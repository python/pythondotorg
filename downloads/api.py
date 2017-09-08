from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication

from pydotorg.drf import BaseAPIViewSet, BaseFilterSet, IsStaffOrReadOnly

from .models import OS, Release, ReleaseFile
from .serializers import OSSerializer, ReleaseSerializer, ReleaseFileSerializer


class OSViewSet(viewsets.ModelViewSet):
    queryset = OS.objects.all()
    serializer_class = OSSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filter_fields = ('name', 'slug')


class ReleaseViewSet(BaseAPIViewSet):
    model = Release
    serializer_class = ReleaseSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filter_fields = (
        'name',
        'slug',
        'is_published',
        'pre_release',
        'version',
        'release_date',
    )


class ReleaseFileFilter(BaseFilterSet):

    class Meta:
        model = ReleaseFile
        fields = {
            'name': ['exact'],
            'slug': ['exact'],
            'description': ['contains'],
            'os': ['exact'],
            'release': ['exact'],
        }


class ReleaseFileViewSet(viewsets.ModelViewSet):
    queryset = ReleaseFile.objects.all()
    serializer_class = ReleaseFileSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filter_class = ReleaseFileFilter
