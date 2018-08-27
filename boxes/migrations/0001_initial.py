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
            name='Box',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('label', models.SlugField(max_length=100, unique=True)),
                ('content', markupfield.fields.MarkupField(rendered_field=True)),
                ('content_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext')),
                ('_content_rendered', models.TextField(editable=False)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='boxes_box_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='boxes_box_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'boxes',
            },
            bases=(models.Model,),
        ),
    ]
