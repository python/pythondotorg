"""Serializers for sponsor API endpoints."""

from rest_framework import serializers

from sponsors.models import GenericAsset
from sponsors.models.enums import LogoPlacementChoices, PublisherChoices


class LogoPlacementSerializer(serializers.Serializer):
    """Serializer for sponsor logo placement data."""

    publisher = serializers.CharField()
    flight = serializers.CharField()
    sponsor = serializers.CharField()
    sponsor_id = serializers.CharField()
    sponsor_slug = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.URLField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    sponsor_url = serializers.URLField()
    level_name = serializers.CharField()
    level_order = serializers.IntegerField()


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for generic sponsorship assets with sponsor metadata."""

    content_type = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    sponsor = serializers.SerializerMethodField()
    sponsor_slug = serializers.SerializerMethodField()

    class Meta:
        """Meta configuration for AssetSerializer."""

        model = GenericAsset
        fields = ["internal_name", "uuid", "value", "content_type", "sponsor", "sponsor_slug"]

    def _get_sponsor_object(self, asset):
        if asset.from_sponsorship:
            return asset.content_object.sponsor
        return asset.content_object

    def get_content_type(self, asset):
        """Return the human-readable content type name for the asset."""
        return asset.content_type.name.title()

    def get_value(self, asset):
        """Return the asset value, or its file URL if it is a file-based asset."""
        if not asset.has_value:
            return ""
        return asset.value if not asset.is_file else asset.value.url

    def get_sponsor(self, asset):
        """Return the sponsor name associated with the asset."""
        return self._get_sponsor_object(asset).name

    def get_sponsor_slug(self, asset):
        """Return the sponsor slug associated with the asset."""
        return self._get_sponsor_object(asset).slug


class FilterLogoPlacementsSerializer(serializers.Serializer):
    """Serializer for filtering logo placements by publisher, flight, and year."""

    publisher = serializers.ChoiceField(
        choices=[(c.value, c.name.replace("_", " ").title()) for c in PublisherChoices],
        required=False,
    )
    flight = serializers.ChoiceField(
        choices=[(c.value, c.name.replace("_", " ").title()) for c in LogoPlacementChoices],
        required=False,
    )
    year = serializers.IntegerField(required=False)

    @property
    def by_publisher(self):
        """Return the validated publisher filter value."""
        return self.validated_data.get("publisher")

    @property
    def by_flight(self):
        """Return the validated flight filter value."""
        return self.validated_data.get("flight")

    @property
    def by_year(self):
        """Return the validated year filter value."""
        return self.validated_data.get("year")

    def skip_logo(self, logo):
        """Return True if this logo should be excluded based on active filters."""
        if self.by_publisher and self.by_publisher != logo.publisher:
            return True
        return bool(self.by_flight and self.by_flight != logo.logo_place)


class FilterAssetsSerializer(serializers.Serializer):
    """Serializer for filtering sponsorship assets by internal name."""

    internal_name = serializers.CharField(max_length=128)
    list_empty = serializers.BooleanField(required=False, default=False)

    @property
    def by_internal_name(self):
        """Return the validated internal name filter value."""
        return self.validated_data["internal_name"]

    @property
    def accept_empty(self):
        """Return whether assets without values should be included."""
        return self.validated_data.get("list_empty", False)
