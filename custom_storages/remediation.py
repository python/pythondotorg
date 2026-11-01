"""Copy referenced public media into private storage and verify each copy before optional public removal."""

import hashlib
from dataclasses import dataclass

from django.core.files.storage import default_storage
from django.core.management.base import CommandError


def _digest(storage, name):
    digest = hashlib.sha256()
    with storage.open(name, "rb") as document:
        for chunk in document.chunks():
            digest.update(chunk)
    return digest.digest()


def copy_and_verify(private_storage, name):
    """Copy ``name`` from public media unless already private, then require matching checksums."""
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


def legacy_names(prefix):
    """Yield every public media name below ``prefix``."""
    try:
        directories, files = default_storage.listdir(prefix)
    except FileNotFoundError:
        return
    for name in files:
        yield f"{prefix}/{name}"
    for directory in directories:
        yield from legacy_names(f"{prefix}/{directory}")


@dataclass
class RemediationResult:
    """Counts and distinct names seen by :func:`remediate_referenced`."""

    names: set
    copied: int = 0
    removed: int = 0
    missing: int = 0
    remaining: int = 0

    def summary(self):
        """Return the operator-facing totals line, without unreferenced-object counts."""
        return (
            f"Copied: {self.copied}; removed legacy copies: {self.removed}; "
            f"referenced legacy copies remaining: {self.remaining}; missing: {self.missing}"
        )


def remediate_referenced(command, names, private_storage, *, apply_changes, delete_legacy):
    """Audit referenced names; with ``apply_changes`` copy and verify, then delete public copies if asked."""
    if delete_legacy and not apply_changes:
        message = "--delete-legacy requires --apply."
        raise CommandError(message)
    result = RemediationResult(names=set())
    for name in names:
        if not name or name in result.names:
            continue
        result.names.add(name)
        private_exists = private_storage.exists(name)
        legacy_exists = default_storage.exists(name)
        if not private_exists and not legacy_exists:
            result.missing += 1
            command.stderr.write(f"[missing] {name}")
            continue
        if not legacy_exists:
            continue
        command.stdout.write(f"[legacy public] {name}")
        if not apply_changes:
            result.remaining += 1
            continue
        result.copied += copy_and_verify(private_storage, name)
        if delete_legacy:
            default_storage.delete(name)
            result.removed += 1
        else:
            result.remaining += 1
    return result
