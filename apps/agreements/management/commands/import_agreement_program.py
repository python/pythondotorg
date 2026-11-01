"""Import privately supplied program and terms configuration without committing commercial content."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.agreements.models import Program, Terms, TermsVersion

if TYPE_CHECKING:
    from django.core.management.base import CommandParser


class Command(BaseCommand):
    """Load a program, immutable terms versions, or both from an operator-supplied JSON file."""

    help = (
        "Import an agreement program and/or terms from private JSON. Use '-' to read stdin. "
        "Existing terms versions never change."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Accept a private file path or stdin."""
        parser.add_argument("path")

    def handle(self, *args: Any, **options: Any) -> None:
        """Validate and apply the import atomically without printing its private content."""
        try:
            text = sys.stdin.read() if options["path"] == "-" else Path(options["path"]).read_text(encoding="utf-8")
            data = json.loads(text)
            with transaction.atomic():
                self._import(data)
        except (OSError, json.JSONDecodeError, ValidationError, KeyError, TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Agreement configuration imported."))

    @staticmethod
    def _import(data: object) -> None:
        if not isinstance(data, dict) or not data or set(data) - {"program", "terms"}:
            msg = "Expected an object with 'program', 'terms', or both."
            raise ValueError(msg)
        for entry in data.get("terms", []):
            metadata = {key: entry[key] for key in ("title", "under_review", "is_public") if key in entry}
            terms, _ = Terms.objects.get_or_create(slug=entry["slug"], defaults=metadata)
            for key, value in metadata.items():
                setattr(terms, key, value)
            terms.full_clean()
            terms.save()
            for item in entry.get("versions", []):
                existing = terms.versions.filter(version=item["version"]).first()
                if existing:
                    if existing.markdown != item["markdown"]:
                        msg = "An imported terms version differs from the stored version; use a new version label."
                        raise ValueError(msg)
                    continue
                version = TermsVersion(
                    terms=terms, version=item["version"], markdown=item["markdown"], notes=item.get("notes", "")
                )
                version.full_clean(exclude=["sha256"])
                version.save()
        if "program" not in data:
            return
        fields = data["program"]
        if not isinstance(fields, dict) or set(fields) - {"slug", "title", "description", "definition", "is_public"}:
            msg = "Program fields: slug, title, description, definition, is_public."
            raise ValueError(msg)
        program = Program.objects.select_for_update().filter(slug=fields["slug"]).first() or Program()
        for key, value in fields.items():
            setattr(program, key, value)
        program.full_clean()
        program.save()
