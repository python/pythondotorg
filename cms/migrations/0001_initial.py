# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import migrations
from django.core.management import call_command


def load_fixture(apps, schema_editor):
    # TODO: This is a temporary hack and will be removed
    # TODO: or at least add a proper rollback
    fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../fixtures'))
    fixture = os.path.join(fixture_dir, 'new-sitetrees.json')
    call_command('loaddata', fixture, verbosity=0)


class Migration(migrations.Migration):

    dependencies = [
        ('sitetree', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_fixture),
    ]
