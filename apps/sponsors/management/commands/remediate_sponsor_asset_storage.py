"""Copy and verify legacy provided and uploaded benefit files before optional public-copy removal."""

from itertools import chain

from django.core.management.base import BaseCommand

from apps.sponsors.models import FileAsset, ProvidedFileAsset, ProvidedFileAssetConfiguration
from apps.sponsors.storage import get_asset_storage
from custom_storages.remediation import remediate_referenced


class Command(BaseCommand):
    help = (
        "Audit benefit file storage; copy with --apply and optionally remove verified public copies. "
        "Image assets stay public and are not touched."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Copy and verify legacy files in private storage.")
        parser.add_argument(
            "--delete-legacy",
            action="store_true",
            help="With --apply, delete referenced public copies only after matching private-copy checksums.",
        )

    def handle(self, *args, **options):
        names = chain(
            FileAsset.objects.values_list("file", flat=True).iterator(),
            ProvidedFileAssetConfiguration.objects.values_list("shared_file", flat=True).iterator(),
            ProvidedFileAsset.objects.values_list("shared_file", flat=True).iterator(),
        )
        result = remediate_referenced(
            self,
            names,
            get_asset_storage(),
            apply_changes=options["apply"],
            delete_legacy=options["delete_legacy"],
        )
        self.stdout.write(f"{result.summary()}.")
        self.stdout.write(
            "This command does not change bucket policies, remove old object versions, or purge caches. "
            "Unreferenced public benefit files cannot be told apart from public image assets and are not audited."
        )
