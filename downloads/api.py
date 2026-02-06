"""REST API endpoints for downloads using Tastypie and Django REST Framework."""

from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from tastypie import fields
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from downloads.models import OS, Release, ReleaseFile
from downloads.serializers import OSSerializer, ReleaseFileSerializer, ReleaseSerializer
from pages.api import PageResource
from pydotorg.drf import BaseAPIViewSet, BaseFilterSet, IsStaffOrReadOnly
from pydotorg.resources import GenericResource, OnlyPublishedAuthorization


class OSResource(GenericResource):
    """Tastypie resource for operating systems."""

    class Meta(GenericResource.Meta):
        """Meta configuration for OSResource."""

        queryset = OS.objects.all()
        resource_name = "downloads/os"
        fields = [
            "name",
            "slug",
            # The following fields won't show up in the response
            # because there is no 'User' relation defined in the API.
            # See 'ReleaseResource.release_page' for an example.
            "creator",
            "last_modified_by",
        ]
        filtering = {
            "name": ("exact",),
            "slug": ("exact",),
        }
        abstract = False


class ReleaseResource(GenericResource):
    """Tastypie resource for Python releases."""

    release_page = fields.ToOneField(PageResource, "release_page", null=True, blank=True)

    class Meta(GenericResource.Meta):
        """Meta configuration for ReleaseResource."""

        queryset = Release.objects.all()
        resource_name = "downloads/release"
        authorization = OnlyPublishedAuthorization()
        fields = [
            "name",
            "slug",
            "creator",
            "last_modified_by",
            "version",
            "is_published",
            "release_date",
            "pre_release",
            "release_page",
            "release_notes_url",
            "show_on_download_page",
            "is_latest",
        ]
        filtering = {
            "name": ("exact",),
            "slug": ("exact",),
            "is_published": ("exact",),
            "pre_release": ("exact",),
            "version": (
                "exact",
                "startswith",
            ),
            "release_date": (ALL,),
        }
        abstract = False


class ReleaseFileResource(GenericResource):
    """Tastypie resource for individual release files."""

    os = fields.ToOneField(OSResource, "os")
    release = fields.ToOneField(ReleaseResource, "release")

    class Meta(GenericResource.Meta):
        """Meta configuration for ReleaseFileResource."""

        queryset = ReleaseFile.objects.all()
        resource_name = "downloads/release_file"
        fields = [
            "name",
            "slug",
            "creator",
            "last_modified_by",
            "os",
            "release",
            "description",
            "is_source",
            "url",
            "gpg_signature_file",
            "md5_sum",
            "sha256_sum",
            "filesize",
            "download_button",
            "sigstore_signature_file",
            "sigstore_cert_file",
            "sigstore_bundle_file",
            "sbom_spdx2_file",
        ]
        filtering = {
            "name": ("exact",),
            "slug": ("exact",),
            "os": ALL_WITH_RELATIONS,
            "release": ALL_WITH_RELATIONS,
            "description": ("contains",),
        }
        abstract = False


# Django Rest Framework


class OSViewSet(viewsets.ModelViewSet):
    """DRF viewset for CRUD operations on operating systems."""

    queryset = OS.objects.all()
    serializer_class = OSSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filterset_fields = ("name", "slug")


class ReleaseViewSet(BaseAPIViewSet):
    """DRF viewset for CRUD operations on releases."""

    model = Release
    serializer_class = ReleaseSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filterset_fields = (
        "name",
        "slug",
        "is_published",
        "pre_release",
        "version",
        "release_date",
    )


class ReleaseFileFilter(BaseFilterSet):
    """Filter set for release file queries."""

    class Meta:
        """Meta configuration for ReleaseFileFilter."""

        model = ReleaseFile
        fields = {
            "name": ["exact"],
            "slug": ["exact"],
            "description": ["contains"],
            "os": ["exact"],
            "release": ["exact"],
        }


class ReleaseFileViewSet(viewsets.ModelViewSet):
    """DRF viewset for CRUD operations on release files."""

    queryset = ReleaseFile.objects.all()
    serializer_class = ReleaseFileSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsStaffOrReadOnly,)
    filterset_class = ReleaseFileFilter

    @action(detail=False, methods=["delete"])
    def delete_by_release(self, request):
        """Delete all release files associated with a given release."""
        release = request.query_params.get("release")
        if release is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # TODO: We can add support for pagination in the future.
        queryset = self.filter_queryset(self.get_queryset())
        # This calls 'mixins.DestroyModelMixin.perform_destroy()'.
        self.perform_destroy(queryset)
        return Response(status=status.HTTP_204_NO_CONTENT)
