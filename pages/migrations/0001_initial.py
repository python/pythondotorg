# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pages.models
import django.core.validators
import markupfield.fields
import re
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentFile',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(upload_to='files/', max_length=500)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=pages.models.page_image_path, max_length=400)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(blank=True)),
                ('title', models.CharField(max_length=500)),
                ('keywords', models.CharField(help_text='HTTP meta-keywords', max_length=1000, blank=True)),
                ('description', models.TextField(help_text='HTTP meta-description', blank=True)),
                ('path', models.CharField(max_length=500, db_index=True, unique=True, validators=[django.core.validators.RegexValidator(message='Please enter a valid URL segment, e.g. "foo" or "foo/bar". Only lowercase letters, numbers, hyphens and periods are allowed.', regex=re.compile('\n    ^\n    /?                      # We can optionally start with a /\n    ([a-z0-9-\\.]+)            # Then at least one path segment...\n    (/[a-z0-9-\\.]+)*        # And then possibly more "/whatever" segments\n    /?                      # Possibly ending with a slash\n    $\n    ', 96))])),
                ('content', markupfield.fields.MarkupField(rendered_field=True)),
                ('content_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext')),
                ('is_published', models.BooleanField(db_index=True, default=True)),
                ('content_type', models.CharField(max_length=150, default='text/html')),
                ('_content_rendered', models.TextField(editable=False)),
                ('template_name', models.CharField(help_text="Example: 'pages/about.html'. If this isn't provided, the system will use 'pages/default.html'.", max_length=100, blank=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='pages_page_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='pages_page_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['title', 'path'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='image',
            name='page',
            field=models.ForeignKey(to='pages.Page', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='documentfile',
            name='page',
            field=models.ForeignKey(to='pages.Page', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
