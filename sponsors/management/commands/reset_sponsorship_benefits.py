from django.core.management.base import BaseCommand
from django.db import transaction
from sponsors.models import Sponsorship, SponsorshipBenefit


class Command(BaseCommand):
    help = "Reset benefits for specified sponsorships to match their current package/year templates"

    def add_arguments(self, parser):
        parser.add_argument(
            "sponsorship_ids",
            nargs="+",
            type=int,
            help="IDs of sponsorships to reset benefits for",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be reset without actually doing it",
        )
        parser.add_argument(
            "--update-year",
            action="store_true",
            help="Update sponsorship year to match the package year",
        )

    def handle(self, *args, **options):
        sponsorship_ids = options["sponsorship_ids"]
        dry_run = options["dry_run"]
        update_year = options["update_year"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        for sid in sponsorship_ids:
            try:
                sponsorship = Sponsorship.objects.get(id=sid)
            except Sponsorship.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Sponsorship {sid} does not exist - skipping")
                )
                continue

            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Sponsorship ID: {sid}")
            self.stdout.write(f"Sponsor: {sponsorship.sponsor.name}")
            self.stdout.write(f"Package: {sponsorship.package.name if sponsorship.package else 'None'}")
            self.stdout.write(f"Sponsorship Year: {sponsorship.year}")
            if sponsorship.package:
                self.stdout.write(f"Package Year: {sponsorship.package.year}")
            self.stdout.write(f"Status: {sponsorship.status}")
            self.stdout.write(f"{'='*60}")

            if not sponsorship.package:
                self.stdout.write(
                    self.style.WARNING("  No package associated - skipping")
                )
                continue

            # Check if year mismatch and update if requested
            target_year = sponsorship.year
            if sponsorship.package.year != sponsorship.year:
                self.stdout.write(
                    self.style.WARNING(
                        f"Year mismatch: Sponsorship year ({sponsorship.year}) != "
                        f"Package year ({sponsorship.package.year})"
                    )
                )
                if update_year:
                    target_year = sponsorship.package.year
                    if not dry_run:
                        sponsorship.year = target_year
                        sponsorship.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Updated sponsorship year to {target_year}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  [DRY RUN] Would update sponsorship year to {target_year}"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Use --update-year to update sponsorship year to {sponsorship.package.year}"
                        )
                    )

            # Get template benefits for this package and target year
            template_benefits = SponsorshipBenefit.objects.filter(
                packages=sponsorship.package,
                year=target_year
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Found {template_benefits.count()} template benefits for year {target_year}"
                )
            )

            if template_benefits.count() == 0:
                self.stdout.write(
                    self.style.ERROR(
                        f"  ERROR: No template benefits found for package "
                        f"'{sponsorship.package.name}' year {target_year}"
                    )
                )
                continue

            reset_count = 0
            missing_count = 0

            # Use transaction to ensure atomicity
            with transaction.atomic():
                from sponsors.models import SponsorBenefit, GenericAsset
                from django.contrib.contenttypes.models import ContentType

                # Get count of current benefits before deletion
                current_count = sponsorship.benefits.count()
                expected_count = template_benefits.count()

                self.stdout.write(
                    f"Current benefits: {current_count}, Expected: {expected_count}"
                )

                # STEP 1: Delete ALL GenericAssets linked to this sponsorship
                sponsorship_ct = ContentType.objects.get_for_model(sponsorship)
                generic_assets = GenericAsset.objects.filter(
                    content_type=sponsorship_ct,
                    object_id=sponsorship.id
                )
                asset_count = generic_assets.count()

                if asset_count > 0:
                    if not dry_run:
                        # Delete each asset individually to handle polymorphic cascade properly
                        deleted_count = 0
                        for asset in generic_assets:
                            asset.delete()
                            deleted_count += 1
                        self.stdout.write(
                            self.style.WARNING(f"  🗑 Deleted {deleted_count} GenericAssets")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  [DRY RUN] Would delete {asset_count} GenericAssets")
                        )

                # STEP 2: Delete ALL existing sponsor benefits (this cascades to features)
                if not dry_run:
                    deleted_count = 0
                    for benefit in sponsorship.benefits.all():
                        self.stdout.write(f"  🗑 Deleting benefit: {benefit.name}")
                        benefit.delete()
                        deleted_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"\nDeleted {deleted_count} existing benefits")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"  [DRY RUN] Would delete all {current_count} existing benefits")
                    )

                # STEP 3: Add all benefits from the package template
                if not dry_run:
                    self.stdout.write(f"\nAdding {expected_count} benefits from {target_year} package...")
                    added_count = 0
                    for template in template_benefits:
                        # Create new benefit with all features from template
                        new_benefit = SponsorBenefit.new_copy(
                            template,
                            sponsorship=sponsorship,
                            added_by_user=False
                        )
                        self.stdout.write(f"  ✓ Added: {template.name}")
                        added_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(f"\nAdded {added_count} benefits with all features")
                    )
                    reset_count = added_count
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  [DRY RUN] Would add {expected_count} benefits from {target_year} package"
                        )
                    )
                    for template in template_benefits[:5]:  # Show first 5
                        self.stdout.write(f"    - {template.name}")
                    if expected_count > 5:
                        self.stdout.write(f"    ... and {expected_count - 5} more")

                if dry_run:
                    # Rollback transaction in dry run
                    transaction.set_rollback(True)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSummary for Sponsorship {sid}: "
                    f"Removed {current_count}, Added {expected_count}"
                )
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\nDRY RUN COMPLETE - No changes were made")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("\nAll sponsorship benefits have been reset!")
            )
