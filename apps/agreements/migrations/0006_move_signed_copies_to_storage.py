"""Move signed copies from the database to private agreement storage, verifying every byte."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from django.core.files.base import ContentFile
from django.db import migrations

if TYPE_CHECKING:
    from django.apps.registry import Apps
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor
    from django.db.models.fields.files import FieldFile

CHUNK_SIZE = 20  # copies are up to 20 MB each


def _stored_sha256(file: FieldFile) -> str:
    digest = hashlib.sha256()
    with file.storage.open(file.name, "rb") as stored:
        for chunk in stored.chunks():
            digest.update(chunk)
    return digest.hexdigest()


def _require_stored_hash(copy: Any) -> None:
    if _stored_sha256(copy.file) != copy.sha256:
        msg = (
            f"Signed copy {copy.pk} ({copy.kind} copy of agreement {copy.agreement_id}) does not match "
            "its recorded SHA-256 once stored. Nothing was migrated; resolve this copy and migrate again."
        )
        raise RuntimeError(msg)


def move_to_storage(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    copies = apps.get_model("agreements", "SignedCopy").objects.using(schema_editor.connection.alias)
    written: list[FieldFile] = []
    try:
        for copy in copies.filter(file__isnull=True).iterator(chunk_size=CHUNK_SIZE):
            copy.file.save(f"{copy.kind}.pdf", ContentFile(bytes(copy.content)), save=False)
            written.append(copy.file)
            _require_stored_hash(copy)
            copies.filter(pk=copy.pk).update(file=copy.file.name)
    except BaseException:
        # The transaction rolls back every row, so no row will refer to the files written so far.
        for file in written:
            file.storage.delete(file.name)
        raise


def restore_to_database(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    """Copy each stored file back into the row. The stored files are kept; delete them by hand if wanted."""
    copies = apps.get_model("agreements", "SignedCopy").objects.using(schema_editor.connection.alias)
    for copy in copies.filter(content__isnull=True).iterator(chunk_size=CHUNK_SIZE):
        with copy.file.open("rb") as stored:
            content = stored.read()
        if hashlib.sha256(content).hexdigest() != copy.sha256:
            msg = f"Stored signed copy {copy.file.name!r} does not match its recorded SHA-256; nothing was restored."
            raise RuntimeError(msg)
        copies.filter(pk=copy.pk).update(content=content)


class Migration(migrations.Migration):
    dependencies = [("agreements", "0005_signedcopy_file")]

    operations = [migrations.RunPython(move_to_storage, restore_to_database)]
