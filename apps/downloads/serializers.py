"""DRF serializers for the downloads API."""

import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.downloads.models import OS, Release, ReleaseFile


class OSSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for operating system data."""

    class Meta:
        """Meta configuration for OSSerializer."""

        model = OS
        fields = ("name", "slug", "resource_uri")


class ReleaseSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for Python release data."""

    class Meta:
        """Meta configuration for ReleaseSerializer."""

        model = Release
        fields = (
            "name",
            "slug",
            "version",
            "is_published",
            "is_latest",
            "release_date",
            "pre_release",
            "release_page",
            "release_notes_url",
            "show_on_download_page",
            "resource_uri",
        )


class ReleaseFileSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for release file data."""

    def validate(self, attrs):
        """Validate release-file URL relationships."""
        attrs = super().validate(attrs)
        release_file = self._release_file_for_validation(attrs)
        try:
            release_file.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs

    def _release_file_for_validation(self, attrs):
        if self.instance is None:
            return ReleaseFile(**attrs)
        release_file = copy.copy(self.instance)
        for attr, value in attrs.items():
            setattr(release_file, attr, value)
        return release_file

    class Meta:
        """Meta configuration for ReleaseFileSerializer."""

        model = ReleaseFile
        fields = (
            "name",
            "slug",
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
            "resource_uri",
            "sigstore_signature_file",
            "sigstore_cert_file",
            "sigstore_bundle_file",
            "sbom_spdx2_file",
        )
