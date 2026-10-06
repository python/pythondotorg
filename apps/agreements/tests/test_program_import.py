"""Protect immutable terms and all-or-nothing private configuration imports."""

import json
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.agreements.models import Program, Terms, TermsVersion
from apps.agreements.tests.catalog_data import make_program


class ProgramImportTests(TestCase):
    def setUp(self):
        self.program = make_program(is_public=False)

    def run_import(self, data):
        with patch("sys.stdin", StringIO(json.dumps(data))):
            call_command("import_agreement_program", "-", stdout=StringIO())

    def test_import_updates_configuration_without_publishing_it(self):
        payload = {
            "program": {
                "slug": self.program.slug,
                "title": "Updated private offering",
                "definition": self.program.definition,
            }
        }
        self.run_import(payload)
        self.program.refresh_from_db()
        self.assertEqual(self.program.title, "Updated private offering")
        self.assertFalse(self.program.is_public)

    def test_conflicting_version_rolls_back_metadata_and_program_changes(self):
        terms = Terms.objects.get(slug=next(iter(self.program.catalog.agreements.values())).terms_slug)
        version = terms.current_version
        original_title = terms.title
        payload = {
            "terms": [
                {
                    "slug": terms.slug,
                    "title": "Must not persist",
                    "versions": [{"version": version.version, "markdown": "Replacement legal text"}],
                }
            ],
            "program": {"slug": self.program.slug, "title": "Must not persist", "definition": self.program.definition},
        }
        with self.assertRaises(CommandError):
            self.run_import(payload)
        terms.refresh_from_db()
        self.assertEqual(terms.title, original_title)
        self.assertEqual(TermsVersion.objects.get(pk=version.pk).markdown, version.markdown)

    def test_invalid_catalog_does_not_leave_imported_terms_behind(self):
        payload = {
            "terms": [
                {
                    "slug": "new-private-terms",
                    "title": "Private terms",
                    "versions": [{"version": "2026-01-01", "markdown": "## Scope\n\nExample scope."}],
                }
            ],
            "program": {"slug": "invalid-program", "title": "Invalid", "definition": {"agreements": []}},
        }
        with self.assertRaises(CommandError):
            self.run_import(payload)
        self.assertFalse(Terms.objects.filter(slug="new-private-terms").exists())
        self.assertFalse(Program.objects.filter(slug="invalid-program").exists())
