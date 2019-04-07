from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response

from tastypie import fields
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from pages.api import PageResource
from pydotorg.resources import GenericResource, OnlyPublishedAuthorization
from pydotorg.drf import BaseAPIViewSet, BaseFilterSet, IsStaffOrReadOnly

from .models import OS, Release, ReleaseFile
from .serializers import OSSerializer, ReleaseSerializer, ReleaseFileSerializer


class OSResource(GenericResource):
    class Meta(GenericResource.Meta):
        queryset = OS.objects.all()
        resource_name = 'downloads/os'
        fields = [
            'name', 'slug',
            # The following fields won't show up in the response
            # because there is no 'User' relation defined in the API.
            # See 'ReleaseResource.release_page' for an example.
            'creator', 'last_modified_by'
        ]
        filtering = {
            'name': ('exact',),
            'slug': ('exact',),
        }
        abstract = False


class ReleaseResource(GenericResource):
    release_page = fields.ToOneField(PageResource, 'release_page', null=True, blank=True)

    class Meta(GenericResource.Meta):
        queryset = Release.objects.all()
        resource_name = 'downloads/release'
        authorization = OnlyPublishedAuthorization()
        fields = [
            'name', 'slug',
            'creator', 'last_modified_by',
            'version', 'is_published', 'release_date', 'pre_release',
            'release_page', 'release_notes_url', 'show_on_download_page',
            'is_latest',
        ]
        filtering = {
            'name': ('exact',),
            'slug': ('exact',),
            'is_published': ('exact',),
            'pre_release': ('exact',),
            'version': ('exact', 'startswith',),
            'release_date': (ALL,)
        }
        abstract = False


class ReleaseFileResource(GenericResource):
    os = fields.ToOneField(OSResource, 'os')
    release = fields.ToOneField(ReleaseResource, 'release')

    class Meta(GenericResource.Meta):
        queryset = ReleaseFile.objects.all()
        resource_name = 'downloads/release_file'
        fields = [
            'name', 'slug',
            'creator', 'last_modified_by',
            'os', 'release', 'description', 'is_source', 'url', 'gpg_signature_file',
            'md5_sum', 'filesize', 'download_button',
        ]
        filtering = {
            'name': ('exact',),
            'slug': ('exact',),
            'os': ALL_WITH_RELATIONS,
            'release': ALL_WITH_RELATIONS,
            'description': ('contains',),
        }
        abstract = False


# Django Rest Framework

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

    @action(detail=False, methods=['delete'])
    def delete_by_release(self, request):
        release = request.query_params.get('release')
        if release is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # TODO: We can add support for pagination in the future.
        queryset = self.filter_queryset(self.get_queryset())
        # This calls 'mixins.DestroyModelMixin.perform_destroy()'.
        self.perform_destroy(queryset)
        return Response(status=status.HTTP_204_NO_CONTENT)
