"""Recognize PDF and DOCX uploads before storing signed contracts."""

import io
import zipfile

from django.core.exceptions import ValidationError
from lxml import etree

_PDF_MAGIC = b"%PDF-"
_PDF_EOF_MARKER = b"%%EOF"
_PDF_TAIL_INSPECT_BYTES = 2048

_ZIP_MAGIC = b"PK\x03\x04"
_DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
_CONTENT_TYPES_NS = "{http://schemas.openxmlformats.org/package/2006/content-types}"
_WORD_NAMESPACES = (
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}",
    "{http://purl.oclc.org/ooxml/wordprocessingml/main}",
)
_DOCX_REQUIRED_ENTRIES = ("word/document.xml", "[Content_Types].xml")

# Limit decompression when inspecting uploads.
_MAX_ZIP_ENTRIES = 512
_MAX_INSPECT_BYTES = 1024 * 1024
_MAX_DOCUMENT_XML_BYTES = 16 * 1024 * 1024


def _looks_like_pdf(file):
    """Return True if ``file`` starts with a PDF header and ends with an EOF marker."""
    file.seek(0)
    if file.read(len(_PDF_MAGIC)) != _PDF_MAGIC:
        return False

    file.seek(0, io.SEEK_END)
    size = file.tell()
    tail_size = min(size, _PDF_TAIL_INSPECT_BYTES)
    file.seek(size - tail_size)
    tail = file.read(tail_size)
    return _PDF_EOF_MARKER in tail


def _looks_like_docx(file):
    """Check the Word document and content-type XML."""
    file.seek(0)
    if file.read(len(_ZIP_MAGIC)) != _ZIP_MAGIC:
        return False

    file.seek(0)
    try:
        with zipfile.ZipFile(file) as archive:
            infos = archive.infolist()
            if len(infos) > _MAX_ZIP_ENTRIES:
                return False

            names = {info.filename for info in infos}
            if not all(entry in names for entry in _DOCX_REQUIRED_ENTRIES):
                return False

            content_types_info = archive.getinfo("[Content_Types].xml")
            document_info = archive.getinfo("word/document.xml")
            if content_types_info.file_size > _MAX_INSPECT_BYTES or document_info.file_size > _MAX_DOCUMENT_XML_BYTES:
                return False
            parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
            content_types = etree.fromstring(archive.read(content_types_info), parser=parser)
            document = etree.fromstring(archive.read(document_info), parser=parser)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, OSError, etree.XMLSyntaxError):
        return False

    return (
        not content_types.getroottree().docinfo.doctype
        and not document.getroottree().docinfo.doctype
        and content_types.tag == _CONTENT_TYPES_NS + "Types"
        and any(
            entry.get("PartName") == "/word/document.xml" and entry.get("ContentType") == _DOCX_CONTENT_TYPE
            for entry in content_types.findall(_CONTENT_TYPES_NS + "Override")
        )
        and document.tag in tuple(namespace + "document" for namespace in _WORD_NAMESPACES)
    )


def validate_signed_contract(file):
    """Check format signatures and restore stream position; this is not a malware scanner."""
    try:
        start = file.tell()
    except (OSError, AttributeError):
        start = 0

    name = getattr(file, "name", "") or ""
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    try:
        if suffix == "pdf":
            valid = _looks_like_pdf(file)
        elif suffix == "docx":
            valid = _looks_like_docx(file)
        else:
            valid = False
    finally:
        file.seek(start)

    if not valid:
        msg = "Upload a PDF or DOCX file."
        raise ValidationError(msg)
