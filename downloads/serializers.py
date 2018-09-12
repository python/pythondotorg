from rest_framework import serializers

from downloads.models import OS, Release, ReleaseFile


class OSSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = OS
        fields = ('name', 'slug', 'resource_uri')


class ReleaseSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Release
        fields = (
            'name',
            'slug',
            'version',
            'is_published',
            'release_date',
            'pre_release',
            'release_page',
            'release_notes_url',
            'show_on_download_page',
            'resource_uri',
        )


class ReleaseFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = ReleaseFile
        fields = (
            'name',
            'slug',
            'os',
            'release',
            'description',
            'is_source',
            'url',
            'gpg_signature_file',
            'md5_sum',
            'filesize',
            'download_button',
            'resource_uri',
        )
