"""Regressions for document access, upload validation, and private-storage migration."""

import io
import zipfile
from tempfile import TemporaryDirectory
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from model_bakery import baker

from apps.sponsors.models import Contract
from apps.sponsors.storage import LocalContractStorage, get_contract_storage
from apps.sponsors.validators import validate_signed_contract

VALID_PDF = b"%PDF-1.4\n%%EOF"


def _docx_bytes(*, valid):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        if valid:
            archive.writestr(
                "[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                'wordprocessingml.document.main+xml"/></Types>',
            )
            archive.writestr(
                "word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>',
            )
        else:
            archive.writestr("hello.txt", "not a Word document")
    return buffer.getvalue()


class ValidateSignedContractTests(SimpleTestCase):
    def test_rejects_executable_uploads_and_disguised_archives(self):
        for name, content in (
            ("c.pdf", b"<html><script>evil()</script></html>"),
            ("c.svg", b"<svg onload='alert(1)'></svg>"),
            ("c.docx", _docx_bytes(valid=False)),
            ("c.html", VALID_PDF),
        ):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                validate_signed_contract(ContentFile(content, name=name))

    def test_pdf_and_docx_validation_preserves_stream_contents_and_position(self):
        for name, content in (("c.pdf", VALID_PDF), ("c.docx", _docx_bytes(valid=True))):
            with self.subTest(name=name):
                document = ContentFile(content, name=name)
                document.seek(3)
                validate_signed_contract(document)
                self.assertEqual(document.read(), content[3:])

    def test_rejects_corrupt_docx_xml_without_losing_stream_position(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("[Content_Types].xml", "wordprocessingml.document")
            archive.writestr("word/document.xml", "<html>not Word</html>")
        document = ContentFile(buffer.getvalue(), name="c.docx")
        document.seek(2)
        with self.assertRaises(ValidationError):
            validate_signed_contract(document)
        self.assertEqual(document.tell(), 2)

    def test_private_storage_rejects_a_public_media_location(self):
        with self.assertRaises(ImproperlyConfigured):
            LocalContractStorage(location=settings.MEDIA_ROOT)


class PrivateFilesTestBase(TestCase):
    def setUp(self):
        public_root = self.enterContext(TemporaryDirectory())
        private_root = self.enterContext(TemporaryDirectory())
        self.enterContext(self.settings(MEDIA_ROOT=public_root, SPONSORS_CONTRACT_STORAGE_ROOT=private_root))
        self.storage = get_contract_storage()
        for name in ("document", "document_docx", "signed_document"):
            self.enterContext(mock.patch.object(getattr(Contract, name).field, "storage", self.storage))
        self.contract = baker.make_recipe("apps.sponsors.tests.empty_contract")


class DownloadContractDocumentViewTests(PrivateFilesTestBase):
    def setUp(self):
        super().setUp()
        self.contract.signed_document.save("test-download.pdf", ContentFile(VALID_PDF))
        self.url = self.contract.signed_document.url

    def test_anonymous_and_inactive_users_cannot_download(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        user = baker.make(settings.AUTH_USER_MODEL, is_superuser=True, is_active=False)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(settings.LOGIN_URL, response.url)

    def test_unrelated_users_and_staff_without_contract_permissions_are_denied(self):
        for is_staff in (False, True):
            with self.subTest(is_staff=is_staff):
                self.client.force_login(baker.make(settings.AUTH_USER_MODEL, is_staff=is_staff))
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_nonstaff_superuser_downloads_private_attachment(self):
        self.client.force_login(baker.make(settings.AUTH_USER_MODEL, is_superuser=True, is_staff=False))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), VALID_PDF)
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertFalse(default_storage.exists(self.contract.signed_document.name))

    def test_nonstaff_group_member_loses_access_after_revocation(self):
        group, _ = Group.objects.get_or_create(name="Sponsorship Admin")
        user = baker.make(settings.AUTH_USER_MODEL, is_staff=False)
        user.groups.add(group)
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(b"".join(response.streaming_content), VALID_PDF)
        user.groups.remove(group)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_django_admin_read_permissions_allow_each_stored_document_type(self):
        for permission in ("view_contract", "change_contract"):
            with self.subTest(permission=permission):
                user = baker.make(settings.AUTH_USER_MODEL, is_staff=True)
                user.user_permissions.add(
                    Permission.objects.get(codename=permission, content_type__app_label="sponsors")
                )
                self.client.force_login(user)
                for name, content in (("document", VALID_PDF), ("document_docx", _docx_bytes(valid=True))):
                    with self.subTest(field=name):
                        document = getattr(self.contract, name)
                        document.save(name + ".bin", ContentFile(content))
                        response = self.client.get(document.url)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(b"".join(response.streaming_content), content)

    def test_untracked_missing_and_traversal_paths_are_not_served(self):
        self.client.force_login(baker.make(settings.AUTH_USER_MODEL, is_superuser=True))
        self.storage.save("untracked.pdf", ContentFile(VALID_PDF))
        for name in ("untracked.pdf", "missing.pdf", "../../outside.pdf"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse("download_contract_document", args=[name])).status_code, 404)
        self.storage.delete(self.contract.signed_document.name)
        self.assertEqual(self.client.get(self.url).status_code, 404)


class RemediateContractStorageCommandTests(PrivateFilesTestBase):
    def setUp(self):
        super().setUp()
        self.name = default_storage.save("sponsors/contracts/legacy.pdf", ContentFile(VALID_PDF))
        self.contract.document.name = self.name
        self.contract.save(update_fields=["document"])

    def test_dry_run_leaves_both_backends_unchanged(self):
        call_command("remediate_contract_storage", stdout=io.StringIO())
        self.assertFalse(self.storage.exists(self.name))
        with default_storage.open(self.name) as original:
            self.assertEqual(original.read(), VALID_PDF)

    def test_copy_then_explicit_public_removal_is_verified_and_idempotent(self):
        call_command("remediate_contract_storage", "--apply", stdout=io.StringIO())
        self.assertTrue(default_storage.exists(self.name))
        with self.storage.open(self.name) as migrated:
            self.assertEqual(migrated.read(), VALID_PDF)
        call_command("remediate_contract_storage", "--apply", "--delete-legacy", stdout=io.StringIO())
        self.assertFalse(default_storage.exists(self.name))
        call_command("remediate_contract_storage", "--apply", "--delete-legacy", stdout=io.StringIO())
        self.contract.refresh_from_db()
        with self.contract.document.open("rb") as migrated:
            self.assertEqual(migrated.read(), VALID_PDF)

    def test_mismatching_private_copy_prevents_public_deletion(self):
        self.storage.save(self.name, ContentFile(b"wrong document"))
        with self.assertRaises(CommandError):
            call_command("remediate_contract_storage", "--apply", "--delete-legacy", stdout=io.StringIO())
        with default_storage.open(self.name) as original:
            self.assertEqual(original.read(), VALID_PDF)

    def test_deletion_requires_explicit_apply(self):
        with self.assertRaises(CommandError):
            call_command("remediate_contract_storage", "--delete-legacy", stdout=io.StringIO())
        self.assertTrue(default_storage.exists(self.name))

    def test_unreferenced_public_objects_are_reported_and_preserved(self):
        name = default_storage.save("sponsors/contracts/unreferenced.pdf", ContentFile(VALID_PDF))
        errors = io.StringIO()
        call_command("remediate_contract_storage", "--apply", "--delete-legacy", stdout=io.StringIO(), stderr=errors)
        self.assertIn(name, errors.getvalue())
        self.assertTrue(default_storage.exists(name))
