"""
The following functions are created for
successstories/migrations/0006_auto_20170726_0824.py:

* convert_to_datetime()
* get_field_list()

"""

import datetime

from xml.etree.ElementTree import fromstring

from docutils.core import publish_doctree
from django.utils.timezone import make_aware, get_current_timezone


def convert_to_datetime(string):
    formats = [
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]
    for fmt in formats:
        try:
            return make_aware(datetime.datetime.strptime(string, fmt),
                              get_current_timezone())
        except ValueError:
            continue


def get_field_list(source):
    dom = publish_doctree(source).asdom()
    tree = fromstring(dom.toxml())
    for field in tree.iter():
        if field.tag == 'field':
            name = next(field.iter(tag='field_name'))
            body = next(field.iter(tag='field_body'))
            yield name.text.lower(), ''.join(body.itertext())
        elif field.tag in ('author', 'date'):
            yield field.tag, ''.join(field.itertext())
