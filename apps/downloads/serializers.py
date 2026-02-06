"""DRF serializers for the downloads API."""

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
