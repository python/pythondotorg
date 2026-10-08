"""Copy and verify legacy contract documents before optional public-copy removal."""

import hashlib
from itertools import chain

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError

from apps.sponsors.models import Contract
from apps.sponsors.storage import get_contract_storage

CONTRACT_FILE_FIELDS = ("document", "document_docx", "signed_document")


def _digest(storage, name):
    digest = hashlib.sha256()
    with storage.open(name, "rb") as document:
        for chunk in document.chunks():
            digest.update(chunk)
    return digest.digest()


def _copy_and_verify(private_storage, name):
    copied = not private_storage.exists(name)
    if copied:
        with default_storage.open(name, "rb") as source:
            saved_name = private_storage.save(name, source)
        if saved_name != name:
            message = f"Private storage returned unexpected key {saved_name!r}; public copy kept."
            raise CommandError(message)
    if _digest(default_storage, name) != _digest(private_storage, name):
        message = f"Checksum mismatch for {name!r}; public copy kept."
        raise CommandError(message)
    return copied


def _legacy_names(prefix):
    try:
        directories, files = default_storage.listdir(prefix)
    except FileNotFoundError:
        return
    for name in files:
        yield f"{prefix}/{name}"
    for directory in directories:
        yield from _legacy_names(f"{prefix}/{directory}")


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
        apply_changes = options["apply"]
        delete_legacy = options["delete_legacy"]
        if delete_legacy and not apply_changes:
            message = "--delete-legacy requires --apply."
            raise CommandError(message)
        private_storage = get_contract_storage()
        names = set()
        copied = removed = missing = remaining = 0
        contracts = Contract.objects.values_list(*CONTRACT_FILE_FIELDS).iterator()
        for name in chain.from_iterable(contracts):
            if not name or name in names:
                continue
            names.add(name)
            private_exists = private_storage.exists(name)
            legacy_exists = default_storage.exists(name)
            if not private_exists and not legacy_exists:
                missing += 1
                self.stderr.write(f"[missing] {name}")
                continue
            if not legacy_exists:
                continue
            self.stdout.write(f"[legacy public] {name}")
            if not apply_changes:
                remaining += 1
                continue
            copied += _copy_and_verify(private_storage, name)
            if delete_legacy:
                default_storage.delete(name)
                removed += 1
            else:
                remaining += 1

        unreferenced = 0
        for name in _legacy_names(Contract.FINAL_VERSION_PDF_DIR.rstrip("/")):
            if name not in names:
                unreferenced += 1
                self.stderr.write(f"[unreferenced legacy object; manual review required] {name}")
        self.stdout.write(
            f"Copied: {copied}; removed legacy copies: {removed}; "
            f"referenced legacy copies remaining: {remaining}; missing: {missing}; "
            f"unreferenced legacy objects: {unreferenced}."
        )
        self.stdout.write(
            "This command does not change bucket policies, remove old object versions, or purge caches. "
            "Deny public access to both contract prefixes and remediate unreferenced objects before deployment."
        )
