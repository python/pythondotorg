"""Copy and verify legacy contract documents before optional public-copy removal."""

from itertools import chain

from django.core.management.base import BaseCommand

from apps.sponsors.models import Contract
from apps.sponsors.storage import get_contract_storage
from custom_storages.remediation import legacy_names, remediate_referenced

CONTRACT_FILE_FIELDS = ("document", "document_docx", "signed_document")


class Command(BaseCommand):
    help = "Audit contract storage; copy with --apply and optionally remove verified public copies."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Copy and verify legacy documents in private storage.")
        parser.add_argument(
            "--delete-legacy",
            action="store_true",
            help="With --apply, delete referenced public copies only after matching private-copy checksums.",
        )

    def handle(self, *args, **options):
        contracts = Contract.objects.values_list(*CONTRACT_FILE_FIELDS).iterator()
        result = remediate_referenced(
            self,
            chain.from_iterable(contracts),
            get_contract_storage(),
            apply_changes=options["apply"],
            delete_legacy=options["delete_legacy"],
        )

        unreferenced = 0
        for name in legacy_names(Contract.FINAL_VERSION_PDF_DIR.rstrip("/")):
            if name not in result.names:
                unreferenced += 1
                self.stderr.write(f"[unreferenced legacy object; manual review required] {name}")
        self.stdout.write(f"{result.summary()}; unreferenced legacy objects: {unreferenced}.")
        self.stdout.write(
            "This command does not change bucket policies, remove old object versions, or purge caches. "
            "Deny public access to both contract prefixes and remediate unreferenced objects before deployment."
        )
