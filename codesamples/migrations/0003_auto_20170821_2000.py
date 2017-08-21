# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codesamples', '0002_auto_20150416_1853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='codesample',
            name='code_markup_type',
            field=models.CharField(choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='html', max_length=30),
        ),
        migrations.AlterField(
            model_name='codesample',
            name='copy_markup_type',
            field=models.CharField(choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')], default='html', max_length=30),
        ),
    ]
