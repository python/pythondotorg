# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields.jsonb
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(blank=True)),
                ('url', models.URLField(max_length=1000, verbose_name='URL', blank=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_link_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_link_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Link',
                'verbose_name_plural': 'Links',
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(blank=True)),
                ('image', models.ImageField(upload_to='community/photos/', blank=True)),
                ('image_url', models.URLField(max_length=1000, verbose_name='Image URL', blank=True)),
                ('caption', models.TextField(blank=True)),
                ('click_through_url', models.URLField(blank=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_photo_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_photo_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'photo',
                'verbose_name_plural': 'photos',
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(blank=True)),
                ('title', models.CharField(max_length=200, blank=True, null=True)),
                ('content', markupfield.fields.MarkupField(rendered_field=True)),
                ('abstract', models.TextField(null=True, blank=True)),
                ('content_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='html')),
                ('_content_rendered', models.TextField(editable=False)),
                ('media_type', models.IntegerField(choices=[(1, 'text'), (2, 'photo'), (3, 'video'), (4, 'link')], default=1)),
                ('source_url', models.URLField(max_length=1000, blank=True)),
                ('meta', django.contrib.postgres.fields.jsonb.JSONField(default={}, blank=True)),
                ('status', models.IntegerField(db_index=True, choices=[(1, 'private'), (2, 'public')], default=1)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_post_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_post_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'post',
                'verbose_name_plural': 'posts',
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(blank=True)),
                ('video_embed', models.TextField(blank=True)),
                ('video_data', models.FileField(upload_to='community/videos/', blank=True)),
                ('caption', models.TextField(blank=True)),
                ('click_through_url', models.URLField(verbose_name='Click Through URL', blank=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_video_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='community_video_modified', blank=True, on_delete=models.CASCADE)),
                ('post', models.ForeignKey(editable=False, null=True, to='community.Post', related_name='related_video', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'video',
                'verbose_name_plural': 'videos',
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='photo',
            name='post',
            field=models.ForeignKey(editable=False, null=True, to='community.Post', related_name='related_photo', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='link',
            name='post',
            field=models.ForeignKey(editable=False, null=True, to='community.Post', related_name='related_link', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
