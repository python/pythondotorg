"""Create realistic test data for the sponsor management UI."""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.sponsors.models import (
    Sponsor,
    SponsorBenefit,
    SponsorContact,
    Sponsorship,
    SponsorshipBenefit,
    SponsorshipCurrentYear,
    SponsorshipPackage,
    SponsorshipProgram,
)

User = get_user_model()

SPONSORS = [
    {
        "name": "CloudScale Inc",
        "desc": "Enterprise cloud infrastructure provider",
        "city": "San Francisco",
        "country": "US",
    },
    {"name": "DataForge Analytics", "desc": "Data analytics and ML platform", "city": "New York", "country": "US"},
    {"name": "SecureNet Solutions", "desc": "Cybersecurity tools and services", "city": "London", "country": "GB"},
    {"name": "DevTools GmbH", "desc": "Developer productivity tools", "city": "Berlin", "country": "DE"},
    {"name": "OpenStack Labs", "desc": "Open source infrastructure company", "city": "Austin", "country": "US"},
    {"name": "AIVentures Corp", "desc": "AI/ML research and deployment platform", "city": "Palo Alto", "country": "US"},
    {"name": "PackagePro", "desc": "Package management and distribution", "city": "Portland", "country": "US"},
    {"name": "WebFramework Ltd", "desc": "Web application framework and hosting", "city": "Seattle", "country": "US"},
    {"name": "PyData Systems", "desc": "Scientific computing and data engineering", "city": "Boston", "country": "US"},
    {"name": "DocuSign Tech", "desc": "Digital document management", "city": "Chicago", "country": "US"},
    {"name": "Serverless.io", "desc": "Serverless deployment platform", "city": "Denver", "country": "US"},
    {"name": "TestRunner AG", "desc": "CI/CD and testing infrastructure", "city": "Zurich", "country": "CH"},
]

# year_offset: 0=current, -1=previous
SCENARIOS = [
    # Current year — Applied (needs review)
    (0, "visionary", 0, "applied", False, 2),
    (1, "sustainability", 0, "applied", False, 5),
    (2, "maintaining", 0, "applied", False, 1),
    (8, "contributing", 0, "applied", False, 10),
    # Current year — Approved (contract pending)
    (3, "contributing", 0, "approved", False, 25),
    (4, "visionary", 0, "approved", True, 18),
    # Current year — Finalized (active)
    (5, "visionary", 0, "finalized", False, 80),
    (6, "sustainability", 0, "finalized", True, 55),
    (9, "maintaining", 0, "finalized", False, 70),
    # Current year — Rejected
    (7, "supporting", 0, "rejected", False, 40),
    # Previous year — Finalized (last year's sponsors, some renewing)
    (0, "visionary", -1, "finalized", False, 400),
    (5, "sustainability", -1, "finalized", False, 380),
    (6, "maintaining", -1, "finalized", False, 370),
    (10, "contributing", -1, "finalized", False, 360),
    (11, "supporting", -1, "finalized", False, 350),
    # Previous year — Rejected
    (3, "supporting", -1, "rejected", False, 390),
]


class Command(BaseCommand):
    help = "Seed realistic sponsor data for the management UI (dev only)"

    def add_arguments(self, parser):
        parser.add_argument("--clean", action="store_true", help="Remove seeded data first")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            msg = "Only run in DEBUG mode."
            raise CommandError(msg)

        if options["clean"]:
            self._clean()
            return

        today = timezone.now().date()
        current_year = today.year

        if not self._ensure_current_year(current_year):
            return
        if not self._ensure_programs_exist():
            return

        user = self._get_or_create_admin_user()
        years = [current_year, current_year - 1]

        if not self._ensure_packages_for_years(years):
            return

        sponsors = self._create_sponsors()
        created_count = self._create_sponsorships(sponsors, user, current_year, today)

        self.stdout.write(
            self.style.SUCCESS(f"Created {created_count} sponsorships across {len(sponsors)} sponsors, years {years}.")
        )
        self.stdout.write("View at: http://localhost:8000/sponsors/manage/sponsorships/")

    def _ensure_current_year(self, current_year):
        cy = SponsorshipCurrentYear.objects.first()
        if cy:
            if cy.year != current_year:
                cy.year = current_year
                cy.save()
            return True
        self.stdout.write("No SponsorshipCurrentYear exists. Create one first.")
        return False

    def _ensure_programs_exist(self):
        if SponsorshipProgram.objects.exists():
            return True
        self.stdout.write("No programs exist. Create at least one SponsorshipProgram first.")
        return False

    def _get_or_create_admin_user(self):
        user, _ = User.objects.get_or_create(
            username="sponsor_admin",
            defaults={"email": "admin@python.org", "is_staff": True, "first_name": "Sponsor", "last_name": "Admin"},
        )
        return user

    def _ensure_packages_for_years(self, years):
        existing_year = SponsorshipPackage.objects.values_list("year", flat=True).distinct().order_by("-year").first()
        if not existing_year:
            self.stdout.write("No packages exist at all. Create packages in Django admin first.")
            return False

        for year in years:
            if not SponsorshipPackage.objects.filter(year=year).exists():
                self.stdout.write(f"  Cloning packages and benefits from {existing_year} to {year}...")
                for pkg in SponsorshipPackage.objects.filter(year=existing_year):
                    pkg.clone(year)
                for ben in SponsorshipBenefit.objects.filter(year=existing_year):
                    ben.clone(year)
        return True

    def _create_sponsors(self):
        sponsors = []
        for data in SPONSORS:
            sponsor, created = Sponsor.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["desc"],
                    "primary_phone": "+1-555-000-0000",
                    "city": data["city"],
                    "country": data["country"],
                    "mailing_address_line_1": "123 Tech Blvd",
                    "postal_code": "10001",
                },
            )
            if created:
                self._create_contacts(sponsor, data)
            sponsors.append(sponsor)
        return sponsors

    def _create_contacts(self, sponsor, data):
        SponsorContact.objects.create(
            sponsor=sponsor,
            name="Primary Contact",
            email=f"contact@{data['name'].lower().replace(' ', '')}.com",
            phone="+1-555-000-0000",
            primary=True,
        )
        SponsorContact.objects.create(
            sponsor=sponsor,
            name="Billing Dept",
            email=f"billing@{data['name'].lower().replace(' ', '')}.com",
            phone="+1-555-000-0001",
            accounting=True,
        )

    def _create_sponsorships(self, sponsors, user, current_year, today):
        created_count = 0
        for sponsor_idx, pkg_slug, year_offset, status, renewal, days_ago in SCENARIOS:
            year = current_year + year_offset
            packages = {p.slug: p for p in SponsorshipPackage.objects.filter(year=year)}
            package = packages.get(pkg_slug)
            if not package:
                continue

            sponsor = sponsors[sponsor_idx]
            if Sponsorship.objects.filter(sponsor=sponsor, year=year, package=package).exists():
                continue

            applied_on = today - timedelta(days=days_ago)
            sp = Sponsorship(
                sponsor=sponsor,
                submited_by=user,
                package=package,
                sponsorship_fee=package.sponsorship_amount,
                year=year,
                for_modified_package=sponsor_idx in (1, 8),
                renewal=renewal,
                applied_on=applied_on,
                status=Sponsorship.APPLIED,
            )
            self._apply_status(sp, status, applied_on)
            sp.save()

            benefits = SponsorshipBenefit.objects.filter(year=year, packages=package).order_by("order")[:5]
            for b in benefits:
                SponsorBenefit.new_copy(b, sponsorship=sp)

            created_count += 1
        return created_count

    @staticmethod
    def _apply_status(sp, status, applied_on):
        if status in ("approved", "finalized"):
            sp.status = Sponsorship.APPROVED
            sp.start_date = applied_on + timedelta(days=10)
            sp.end_date = sp.start_date + timedelta(days=365)
            sp.approved_on = applied_on + timedelta(days=5)
            sp.locked = True

        if status == "finalized":
            sp.status = Sponsorship.FINALIZED
            sp.finalized_on = sp.approved_on + timedelta(days=7)

        if status == "rejected":
            sp.status = Sponsorship.REJECTED
            sp.rejected_on = applied_on + timedelta(days=3)
            sp.locked = True

    def _clean(self):
        names = [s["name"] for s in SPONSORS]
        Sponsorship.objects.filter(sponsor__name__in=names).delete()
        Sponsor.objects.filter(name__in=names).delete()
        User.objects.filter(username="sponsor_admin").delete()
        self.stdout.write(self.style.SUCCESS("Cleaned seeded sponsor data."))
