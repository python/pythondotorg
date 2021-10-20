from rest_framework import permissions
from rest_framework import serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from sponsors.models import BenefitFeature, LogoPlacement, Sponsorship


class LogoPlacementSerializer(serializers.Serializer):
    publisher = serializers.CharField()
    flight = serializers.CharField()
    sponsor = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.URLField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    sponsor_url = serializers.URLField()
    level_name = serializers.CharField()
    level_order = serializers.IntegerField()


class SponsorPublisherPermission(permissions.BasePermission):
    message = 'Must have publisher permission.'

    def has_permission(self, request, view):
        user = request.user
        if request.user.is_superuser or request.user.is_staff:
            return True
        return user.has_perm("sponsors.sponsor_publisher")


class LogoPlacementeAPIList(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [SponsorPublisherPermission]
    serializer_class = LogoPlacementSerializer

    def get(self, request, *args, **kwargs):
        placements = []

        sponsorships = Sponsorship.objects.enabled().with_logo_placement()
        for sponsorship in sponsorships.select_related("sponsor").iterator():
            sponsor = sponsorship.sponsor
            base_data = {
                "sponsor": sponsor.name,
                "level_name": sponsorship.level_name,
                "level_order": sponsorship.package.order,
                "description": sponsor.description,
                "logo": sponsor.web_logo.url,
                "sponsor_url": sponsor.landing_page_url,
                "start_date": sponsorship.start_date,
                "end_date": sponsorship.end_date,
            }

            benefits = BenefitFeature.objects.filter(sponsor_benefit__sponsorship_id=sponsorship.pk)
            for logo in benefits.instance_of(LogoPlacement):
                placement = base_data.copy()
                placement["publisher"] = logo.publisher
                placement["flight"] = logo.logo_place
                placements.append(placement)

        serializer = LogoPlacementSerializer(placements, many=True)
        return Response(serializer.data)
