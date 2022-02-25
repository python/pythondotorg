from django.utils.text import slugify
from django.urls import reverse

from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from sponsors.models import BenefitFeature, LogoPlacement, Sponsorship
from sponsors.serializers import LogoPlacementSerializer, FilterLogoPlacementsSerializer


class SponsorPublisherPermission(permissions.BasePermission):
    message = 'Must have publisher permission.'

    def has_permission(self, request, view):
        user = request.user
        if request.user.is_superuser or request.user.is_staff:
            return True
        return user.has_perm("sponsors.sponsor_publisher")


class LogoPlacementeAPIList(APIView):
    permission_classes = [SponsorPublisherPermission]
    serializer_class = LogoPlacementSerializer

    def get(self, request, *args, **kwargs):
        placements = []
        logo_filters = FilterLogoPlacementsSerializer(data=request.GET)
        if not logo_filters.is_valid():
            return Response(logo_filters.errors, status=400)

        sponsorships = Sponsorship.objects.enabled().with_logo_placement()
        for sponsorship in sponsorships.select_related("sponsor").iterator():
            sponsor = sponsorship.sponsor
            base_data = {
                "sponsor": sponsor.name,
                "sponsor_slug": sponsor.slug,
                "level_name": sponsorship.level_name,
                "level_order": sponsorship.package.order,
                "description": sponsor.description,
                "logo": sponsor.web_logo.url,
                "sponsor_url": sponsor.landing_page_url,
                "start_date": sponsorship.start_date,
                "end_date": sponsorship.end_date,
            }

            benefits = BenefitFeature.objects.filter(sponsor_benefit__sponsorship_id=sponsorship.pk)
            logos = [l for l in benefits.instance_of(LogoPlacement) if not logo_filters.skip_logo(l)]
            for logo in logos:
                placement = base_data.copy()
                placement["publisher"] = logo.publisher
                placement["flight"] = logo.logo_place
                if logo.describe_as_sponsor:
                    placement["description"] = f"{sponsor.name} is a {sponsorship.level_name} sponsor of the Python Software Foundation."
                if logo.link_to_sponsors_page:
                    placement["sponsor_url"] = request.build_absolute_uri(reverse('psf-sponsors') + f"#{slugify(sponsor.name)}")
                placements.append(placement)

        serializer = LogoPlacementSerializer(placements, many=True)
        return Response(serializer.data)
