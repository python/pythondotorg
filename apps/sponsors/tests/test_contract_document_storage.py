"""Regressions for document access, upload validation, and private-storage migration."""

import io
import zipfile

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import SimpleTestCase

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
