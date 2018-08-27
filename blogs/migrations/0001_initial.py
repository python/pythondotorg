# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogEntry',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('summary', models.TextField(blank=True)),
                ('pub_date', models.DateTimeField()),
                ('url', models.URLField(verbose_name='URL')),
            ],
            options={
                'verbose_name': 'Blog Entry',
                'verbose_name_plural': 'Blog Entries',
                'get_latest_by': 'pub_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='blogs_contributor_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='blogs_contributor_modified', blank=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='blog_contributor', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Contributor',
                'verbose_name_plural': 'Contributors',
                'ordering': ('user__last_name', 'user__first_name'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('website_url', models.URLField()),
                ('feed_url', models.URLField()),
                ('last_import', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FeedAggregate',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(help_text='Where this appears on the site')),
                ('feeds', models.ManyToManyField(to='blogs.Feed')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelatedBlog',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('name', models.CharField(help_text='Internal Name', max_length=100)),
                ('feed_url', models.URLField(verbose_name='Feed URL')),
                ('blog_url', models.URLField(verbose_name='Blog URL')),
                ('blog_name', models.CharField(help_text='Displayed Name', max_length=200)),
                ('last_entry_published', models.DateTimeField(db_index=True)),
                ('last_entry_title', models.CharField(max_length=500)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='blogs_relatedblog_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='blogs_relatedblog_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Related Blog',
                'verbose_name_plural': 'Related Blogs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('name', models.CharField(max_length=100)),
                ('url', models.URLField(verbose_name='URL')),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='blogs_translation_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='blogs_translation_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name': 'Translation',
                'verbose_name_plural': 'Translations',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='blogentry',
            name='feed',
            field=models.ForeignKey(to='blogs.Feed', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
