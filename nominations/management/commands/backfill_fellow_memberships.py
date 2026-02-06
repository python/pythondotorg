import csv

from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import Membership, User


class Command(BaseCommand):
    help = (
        "One-time backfill script to create Membership records (type=FELLOW) "
        "from a CSV data source."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            required=True,
            help="Path to the CSV file with columns: email, first_name, last_name, city, country",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Print what would be done without making changes.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN mode enabled. No changes will be made.\n"))

        rows = self._read_csv(csv_path)
        if rows is None:
            return

        if dry_run:
            self._process_rows(rows, dry_run=True)
        else:
            with transaction.atomic():
                self._process_rows(rows, dry_run=False)

    def _read_csv(self, csv_path):
        """Read and return rows from the CSV file, or None on error."""
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"CSV file not found: {csv_path}"))
            return None
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error reading CSV: {e}"))
            return None

    def _process_rows(self, rows, *, dry_run):
        """Process all CSV rows, creating users and memberships as needed."""
        created_count = 0
        skipped_count = 0
        error_count = 0

        for line_num, row in enumerate(rows, start=2):  # start=2 because line 1 is the header
            email = (row.get("email") or "").strip()
            if not email:
                self.stderr.write(
                    self.style.WARNING(f"Line {line_num}: Skipping row with missing/empty email.")
                )
                skipped_count += 1
                continue

            first_name = (row.get("first_name") or "").strip()
            last_name = (row.get("last_name") or "").strip()
            city = (row.get("city") or "").strip()
            country = (row.get("country") or "").strip()
            legal_name = f"{first_name} {last_name}".strip()

            try:
                result = self._process_single_row(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    legal_name=legal_name,
                    city=city,
                    country=country,
                    dry_run=dry_run,
                    line_num=line_num,
                )
                if result == "created":
                    created_count += 1
                elif result == "skipped":
                    skipped_count += 1
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Line {line_num}: Error processing {email}: {e}")
                )
                error_count += 1

        # Print summary
        self.stdout.write("")
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"{prefix}Summary:"))
        self.stdout.write(f"  Created: {created_count}")
        self.stdout.write(f"  Skipped: {skipped_count}")
        self.stdout.write(f"  Errors:  {error_count}")

    def _process_single_row(self, *, email, first_name, last_name, legal_name, city, country, dry_run, line_num):
        """
        Process a single CSV row. Returns 'created' or 'skipped'.
        Raises on unexpected errors.
        """
        email_lower = email.lower()

        # Look up existing user (case-insensitive email match)
        try:
            user = User.objects.get(email__iexact=email_lower)
        except User.DoesNotExist:
            user = None
        except User.MultipleObjectsReturned:
            self.stderr.write(
                self.style.WARNING(
                    f"Line {line_num}: Multiple users found for {email}. Skipping."
                )
            )
            return "skipped"

        # Check for existing membership of any type
        if user is not None:
            try:
                existing = user.membership
                if existing is not None:
                    if existing.membership_type == Membership.FELLOW:
                        self.stdout.write(
                            f"Line {line_num}: {email} already has a Fellow membership. Skipping."
                        )
                    else:
                        membership_label = existing.get_membership_type_display()
                        self.stderr.write(
                            self.style.WARNING(
                                f"Line {line_num}: {email} already has a '{membership_label}' "
                                f"membership. Skipping."
                            )
                        )
                    return "skipped"
            except Membership.DoesNotExist:
                pass  # No membership yet, proceed to create one

        if dry_run:
            action = "create user + " if user is None else ""
            self.stdout.write(
                f"[DRY RUN] Line {line_num}: Would {action}create Fellow membership "
                f"for {email} ({legal_name})"
            )
            return "created"

        # Create user if needed
        if user is None:
            username = self._generate_username(email_lower)
            user = User.objects.create_user(
                username=username,
                email=email_lower,
                first_name=first_name,
                last_name=last_name,
            )
            self.stdout.write(f"Line {line_num}: Created user '{username}' for {email}.")

        # Create the Fellow membership
        Membership.objects.create(
            creator=user,
            membership_type=Membership.FELLOW,
            legal_name=legal_name,
            preferred_name=first_name,
            email_address=email_lower,
            city=city,
            country=country,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Line {line_num}: Created Fellow membership for {email} ({legal_name})."
            )
        )
        return "created"

    def _generate_username(self, email):
        """
        Generate a unique username from the email address.
        Uses the local part of the email, appending a numeric suffix if needed.
        """
        base = email.split("@")[0]
        # Sanitize: keep only alphanumeric, dots, hyphens, underscores
        base = "".join(c for c in base if c.isalnum() or c in ".-_")
        if not base:
            base = "fellow"

        username = base
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{suffix}"
            suffix += 1
        return username
