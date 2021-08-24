import csv

from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from sponsors.enums import LogoPlacementChoices, PublisherChoices


class LogoPlacementSerializer(serializers.Serializer):
    publisher = serializers.CharField()
    flight = serializers.CharField()
    sponsor = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.URLField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    sponsor_url = serializers.URLField()


# TODO Currently this endpoint only lists sponsors from pypi sponsors CSV.
# Once we have all sponsorship data input into pydotorg, we should be
# able to change this view to fetch data from the database instead.
class LogoPlacementeAPIList(APIView):
    serializer_class = LogoPlacementSerializer

    def get(self, request, *args, **kwargs):
        placements = []

        with open("pypi-sponsors.csv", "r") as fd:
            for row in csv.DictReader(fd):
                if row["is_active"] != "t":
                    continue

                base_data = {
                    "publisher": PublisherChoices.PYPI.value,
                    "sponsor": row["name"],
                    "description": row["activity_markdown"],
                    "logo": row["color_logo_url"],
                    "start_date": None,
                    "end_date": None,
                    "sponsor_url": row["link_url"],
                }

                sponsors_page_keys = ["psf_sponsor", "infra_sponsor", "one_time"]
                if any([row[k] == "t" for k in sponsors_page_keys]):
                    placement = base_data.copy()
                    placement["flight"] = LogoPlacementChoices.SPONSORS_PAGE.value
                    placements.append(placement)

                if row["sidebar"] == "t":
                    placement = base_data.copy()
                    placement["flight"] = LogoPlacementChoices.SIDEBAR.value
                    placement["sponsor_url"] = "https://pypi.org/sponsors/"
                    placements.append(placement)

        serializer = LogoPlacementSerializer(placements, many=True)
        return Response(serializer.data)
