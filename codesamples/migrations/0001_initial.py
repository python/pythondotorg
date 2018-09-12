# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CodeSample',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('code', markupfield.fields.MarkupField(rendered_field=True, blank=True)),
                ('code_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='html', blank=True)),
                ('copy', markupfield.fields.MarkupField(rendered_field=True, blank=True)),
                ('_code_rendered', models.TextField(editable=False)),
                ('copy_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='html', blank=True)),
                ('is_published', models.BooleanField(db_index=True, default=False)),
                ('_copy_rendered', models.TextField(editable=False)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='codesamples_codesample_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='codesamples_codesample_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'sample',
                'verbose_name_plural': 'samples',
            },
            bases=(models.Model,),
        ),
    ]
