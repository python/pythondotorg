"""Parsers for reading legacy content.ht and content.rst page files."""

import email
from pathlib import Path

import chardet


def read_content_file(dirpath):
    """Parse the content file in a directory as an email message.

    (str): (str, email.Message)
    Given a directory path, figure out the file holding the content
    for that directory and parse it as an email message.

    Copied from old Python.org build process.
    """
    # Read page content
    c_ht = Path(dirpath) / "content.ht"
    c_rst = Path(dirpath) / "content.rst"

    if c_ht.exists():
        raw_input = c_ht.read_bytes()
        detection = chardet.detect(raw_input)

        with c_ht.open(encoding=detection["encoding"], errors="ignore") as file_handle:
            msg = email.message_from_file(file_handle)

        filename = str(c_ht)

    elif c_rst.exists():
        rst_text = c_rst.read_text()
        rst_msg = f"""Content-type: text/x-rst

{rst_text.lstrip()}"""
        msg = email.message_from_string(rst_msg)
        filename = str(c_rst)

    else:
        return None, None

    return filename, msg


def determine_page_content_type(content):
    """Attempt to determine if content is ReST or HTML."""
    tags = ["<p>", "<ul>", "<h1>", "<h2>", "<h3>", "<pre>", "<br", "<table>"]
    content_type = "restructuredtext"
    content = content.lower()

    for t in tags:
        if t in content:
            content_type = "html"

    return content_type


def parse_page(dirpath):
    """Parse a page given a relative file path."""
    filename, msg = read_content_file(dirpath)

    content = msg.get_payload()
    content_type = determine_page_content_type(content)

    return {
        "headers": dict(msg.items()),
        "content": content,
        "content_type": content_type,
        "filename": filename,
    }
