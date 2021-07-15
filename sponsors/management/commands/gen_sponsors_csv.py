import csv
from django.core.management import BaseCommand
from django.template.defaultfilters import slugify

from sponsors.models import Sponsorship, Contract

# This command works as a faster entrypoint to generate a CSV file
# with all the sponsor data required by the sponsor placement server
# Python.org will use to display sponsors' logo. This command can
# become an optional one once such operation is enabled via admin.

class Command(BaseCommand):
    """
    Generate CSV with sponsors data to be sent to sponsor placement server
    """
    help = "Generate CSV with sponsors data to be sent to sponsor placement server"

    def handle(self, **options):
        qs = Sponsorship.objects.finalized().select_related('sponsor')
        if not qs.exists():
            print("There's no finalized Sponsorship.")
            return

        rows = []
        for sponsorship in qs.iterator():
            base_row = {
                "sponsor": sponsorship.sponsor.name,
                "description": sponsorship.sponsor.description,
                "logo": sponsorship.sponsor.web_logo.url,
                "sponsor_url": sponsorship.sponsor.landing_page_url,
                "start_date": sponsorship.start_date.isoformat(),
                "end_date": sponsorship.end_date.isoformat(),
            }

            benefits = sponsorship.benefits.select_related('sponsorship_benefit')
            for benefit in benefits.iterator():
                # TODO implement this as DB objects not hardcoded checks
                # - check for logo placements
                # - use the program to determine the publisher
                # - use the flight to determine the placement (footer/sidebar/sponsor etc)
                flight_mapping = {
                    # Foundation
                    "Logo on python.org": "sponsors",
                    "jobs.python.org support": "jobs",
                    "Logo listed on PSF blog": "blogspot",
                    # Pycon
                    "PyCon website Listing": "sponsors",
                    # Pypi
                    "Logo on the PyPI sponsors page": "sponsors",
                    "Logo in a prominent position on the PyPI project detail page": "sidebar",
                    "Logo on the PyPI footer": "footer",
                    # Core dev
                    "docs.python.org recognition": "docs",
                    "Logo on python.org/downloads/": "docs-download",
                    "Logo recognition on devguide.python.org/": "devguide"
                }

                publisher = benefit.program.name
                flight = flight_mapping.get(benefit.name)
                if publisher and flight:
                    row = base_row.copy()

                    if not sponsorship.sponsor.web_logo:
                        print(f"WARNING: sponsor {sponsorship.sponsor} without logo")
                        continue

                    if publisher == "Foundation" and flight in ["jobs", "blogspot"]:
                        row["sponsor_url"] = "https://www.python.org/psf/sponsorship/sponsors/"

                    row["publisher"] = publisher
                    row["flight"] = slugify(publisher) + '-' + flight
                    rows.append(row)

        columns = [
            "publisher",
            "flight",
            "sponsor",
            "description",
            "logo",
            "start_date",
            "end_date",
            "sponsor_url",
        ]
        with open('sponsors.csv', 'w') as fd:
            writer = csv.DictWriter(fd, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        print(f"Done!")
