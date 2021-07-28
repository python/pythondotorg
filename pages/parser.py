import chardet
import email
import os


def read_content_file(dirpath):
    """(str): (str, email.Message)
    Given a directory path, figure out the file holding the content
    for that directory and parse it as an email message.

    Copied from old Python.org build process.
    """
    # Read page content
    c_ht = os.path.join(dirpath, 'content.ht')
    c_rst = os.path.join(dirpath, 'content.rst')

    if os.path.exists(c_ht):
        raw_input = open(c_ht, 'rb').read()
        detection = chardet.detect(raw_input)

        input = open(c_ht, encoding=detection['encoding'], errors='ignore')
        msg = email.message_from_file(input)

        filename = c_ht

    elif os.path.exists(c_rst):
        rst_text = open(c_rst).read()
        rst_msg = """Content-type: text/x-rst

%s""" % rst_text.lstrip()
        msg = email.message_from_string(rst_msg)
        filename = c_rst

    else:
        return None, None

    return filename, msg


def determine_page_content_type(content):
    """ Attempt to determine if content is ReST or HTML """
    tags = ['<p>', '<ul>', '<h1>', '<h2>', '<h3>', '<pre>', '<br', '<table>']
    content_type = 'restructuredtext'
    content = content.lower()

    for t in tags:
        if t in content:
            content_type = 'html'

    return content_type


def parse_page(dirpath):
    """ Parse a page given a relative file path """
    filename, msg = read_content_file(dirpath)

    content = msg.get_payload()
    content_type = determine_page_content_type(content)

    data = {
        'headers': dict(msg.items()),
        'content': content,
        'content_type': content_type,
        'filename': filename,
    }

    return data
