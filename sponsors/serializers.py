
from rest_framework import serializers
from sponsors.models.enums import PublisherChoices, LogoPlacementChoices

class LogoPlacementSerializer(serializers.Serializer):
    publisher = serializers.CharField()
    flight = serializers.CharField()
    sponsor = serializers.CharField()
    sponsor_slug = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.URLField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    sponsor_url = serializers.URLField()
    level_name = serializers.CharField()
    level_order = serializers.IntegerField()


class FilterLogoPlacementsSerializer(serializers.Serializer):
    publisher = serializers.ChoiceField(
        choices=[(c.value, c.name.replace("_", " ").title()) for c in PublisherChoices],
        required=False,
    )
    flight = serializers.ChoiceField(
        choices=[(c.value, c.name.replace("_", " ").title()) for c in LogoPlacementChoices],
        required=False,
    )

    @property
    def by_publisher(self):
        return self.validated_data.get("publisher")

    @property
    def by_flight(self):
        return self.validated_data.get("flight")

    def skip_logo(self, logo):
        if self.by_publisher and self.by_publisher != logo.publisher:
            return True
        if self.by_flight and self.by_flight != logo.logo_place:
            return True
        else:
            return False
