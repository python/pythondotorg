# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('company_name', models.CharField(max_length=500)),
                ('company_url', models.URLField()),
                ('author', models.CharField(max_length=500)),
                ('pull_quote', models.TextField()),
                ('content', markupfield.fields.MarkupField(rendered_field=True)),
                ('content_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext')),
                ('is_published', models.BooleanField(db_index=True, default=False)),
                ('_content_rendered', models.TextField(editable=False)),
                ('featured', models.BooleanField(help_text='Set to use story in the supernav', default=False)),
                ('weight', models.IntegerField(help_text='Percentage weight given to display, enter 11 for 11% of views. Warnings will be given in flash messages if total of featured Stories is not equal to 100%', default=0)),
                ('image', models.ImageField(upload_to='successstories', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'story',
                'verbose_name_plural': 'stories',
                'ordering': ('-created',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StoryCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'story category',
                'verbose_name_plural': 'story categories',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='story',
            name='category',
            field=models.ForeignKey(to='successstories.StoryCategory', related_name='success_stories', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='story',
            name='company',
            field=models.ForeignKey(null=True, to='companies.Company', related_name='success_stories', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='story',
            name='creator',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='successstories_story_creator', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='story',
            name='last_modified_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='successstories_story_modified', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
