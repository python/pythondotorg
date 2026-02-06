"""Management command to create test sponsor and contract data for testing (development only)."""

import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.sponsors.models import Contract, Sponsor, SponsorContact, Sponsorship, SponsorshipPackage

User = get_user_model()


class Command(BaseCommand):
    help = "Create test sponsor and contract data for testing contract display (development only)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete existing test data before creating new data",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force execution even in non-DEBUG mode (use with extreme caution)",
        )

    def handle(self, *args, **options):
        # Production safety check
        if not settings.DEBUG and not options["force"]:
            msg = "This command cannot be run in production (DEBUG=False). This command creates test data and should only be used in development environments."
            raise CommandError(msg)
        if options["clean"]:
            self._clean_test_data()

        run_id = str(uuid.uuid4())[:8]
        self.stdout.write(f"Creating test sponsor and contract data (Run ID: {run_id})...")

        User.objects.get_or_create(
            username="test_sponsor_user",
            defaults={"email": "test@sponsor.com", "first_name": "Test", "last_name": "User"},
        )

        current_year = timezone.now().date().year - 5
        package, _created = SponsorshipPackage.objects.get_or_create(
            name="Test Package - Gold",
            year=current_year,
            defaults={"sponsorship_amount": 10000, "advertise": True, "logo_dimension": 200, "slug": "test-gold"},
        )

        sponsor_name = f"Test Sponsor Corp {run_id}"
        sponsor = Sponsor.objects.create(
            name=sponsor_name,
            description=f"A test sponsor company for development and testing ({run_id})",
            landing_page_url=f"https://test-sponsor-{run_id}.com",
            twitter_handle=f"@testsponsor{run_id}",
            primary_phone="+1-555-0123",
            mailing_address_line_1=f"123 Test Street {run_id}",
            city="Test City",
            state="Test State",
            postal_code="12345",
            country="US",
        )

        SponsorContact.objects.create(
            sponsor=sponsor,
            name=f"John Test Contact {run_id}",
            email=f"john@testsponsor{run_id}.com",
            phone="+1-555-0123",
            primary=True,
        )

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=365)
        current_test_year = start_date.year + 1

        sponsorships = self._create_sponsorships(sponsor, package, start_date, end_date, current_test_year)

        contract = self._create_contract(sponsorships[2][1], sponsor_name, run_id)

        self._print_summary(sponsor, package, contract, sponsorships)

    def _clean_test_data(self):
        self.stdout.write("Cleaning existing test data...")
        Contract.objects.filter(sponsorship__sponsor__name__startswith="Test Sponsor").delete()
        Sponsorship.objects.filter(sponsor__name__startswith="Test Sponsor").delete()
        Sponsor.objects.filter(name__startswith="Test Sponsor").delete()
        SponsorshipPackage.objects.filter(name__startswith="Test Package").delete()

    def _create_sponsorships(self, sponsor, package, start_date, end_date, year):
        sponsorships = []

        sponsorship_applied = Sponsorship.objects.create(
            sponsor=sponsor,
            package=package,
            status=Sponsorship.APPLIED,
            applied_on=start_date,
            for_modified_package=False,
            year=year,
            sponsorship_fee=package.sponsorship_amount,
        )
        sponsorships.append(("Applied", sponsorship_applied))

        sponsorship_approved = Sponsorship.objects.create(
            sponsor=sponsor,
            package=package,
            status=Sponsorship.APPROVED,
            start_date=start_date,
            end_date=end_date,
            applied_on=start_date - timedelta(days=5),
            approved_on=start_date,
            for_modified_package=False,
            year=year,
            sponsorship_fee=package.sponsorship_amount,
        )
        sponsorships.append(("Approved", sponsorship_approved))

        sponsorship_finalized = Sponsorship.objects.create(
            sponsor=sponsor,
            package=package,
            status=Sponsorship.FINALIZED,
            start_date=start_date,
            end_date=end_date,
            applied_on=start_date - timedelta(days=10),
            approved_on=start_date - timedelta(days=5),
            finalized_on=start_date,
            for_modified_package=False,
            year=year,
            sponsorship_fee=package.sponsorship_amount,
        )
        sponsorships.append(("Finalized", sponsorship_finalized))

        sponsorship_rejected = Sponsorship.objects.create(
            sponsor=sponsor,
            package=package,
            status=Sponsorship.REJECTED,
            applied_on=start_date - timedelta(days=25),
            rejected_on=start_date - timedelta(days=20),
            for_modified_package=False,
            year=year,
            sponsorship_fee=package.sponsorship_amount,
            locked=True,
        )
        sponsorships.append(("Rejected", sponsorship_rejected))

        return sponsorships

    def _create_contract(self, sponsorship, sponsor_name, run_id):
        dummy_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        contract = Contract.objects.create(
            sponsorship=sponsorship,
            status=Contract.AWAITING_SIGNATURE,
            revision=1,
            sponsor_info=f"{sponsor_name}\n123 Test Street {run_id}\nTest City, Test State 12345\nUS",
            sponsor_contact=f"John Test Contact {run_id}\njohn@testsponsor{run_id}.com\n+1-555-0123",
        )
        contract.document.save(f"test_contract_{run_id}.pdf", ContentFile(dummy_pdf_content), save=True)
        return contract

    def _print_summary(self, sponsor, package, contract, sponsorships):
        self.stdout.write(self.style.SUCCESS("Successfully created test data:"))
        self.stdout.write(f"- Sponsor: {sponsor.name} (ID: {sponsor.id})")
        self.stdout.write(f"- Package: {package.name}")
        self.stdout.write(f"- Contract: {contract} (ID: {contract.id})")

        self.stdout.write("\nCreated Sponsorships with ALL status types:")
        for status_name, sponsorship_obj in sponsorships:
            self.stdout.write(f"  {status_name}: ID {sponsorship_obj.id} - {sponsorship_obj}")

        self.stdout.write("\nTesting URLs:")
        self.stdout.write("Admin Sponsorships List:")
        self.stdout.write("  http://localhost:8000/admin/sponsors/sponsorship/")

        self.stdout.write("\nTest Status Transitions:")
        approved_id = sponsorships[1][1].id
        self.stdout.write(f"  Cancel Approved: http://localhost:8000/admin/sponsors/sponsorship/{approved_id}/cancel")

        self.stdout.write("\nView Sponsorship Details:")
        for status_name, sponsorship_obj in sponsorships:
            self.stdout.write(
                f"  {status_name}: http://localhost:8000/admin/sponsors/sponsorship/{sponsorship_obj.id}/change/"
            )

        self.stdout.write("\nContract Display:")
        self.stdout.write(f"  http://localhost:8000/admin/sponsors/contract/{contract.id}/preview")
        self.stdout.write(f"  http://localhost:8000/admin/sponsors/contract/{contract.id}/change/")
