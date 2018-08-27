# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import events.models
import markupfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarm',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('trigger', models.PositiveSmallIntegerField(verbose_name='hours before the event occurs', default=24)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='events_alarm_creator', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('url', models.URLField(verbose_name='URL iCal', blank=True, null=True)),
                ('rss', models.URLField(verbose_name='RSS Feed', blank=True, null=True)),
                ('embed', models.URLField(verbose_name='URL embed', blank=True, null=True)),
                ('twitter', models.URLField(verbose_name='Twitter feed', blank=True, null=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.CharField(max_length=255, blank=True, null=True)),
                ('creator', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='events_calendar_creator', blank=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='events_calendar_modified', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, blank=True)),
                ('updated', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('uid', models.CharField(max_length=200, blank=True, null=True)),
                ('title', models.CharField(max_length=200)),
                ('description', markupfield.fields.MarkupField(rendered_field=True)),
                ('description_markup_type', models.CharField(max_length=30, choices=[('', '--'), ('html', 'html'), ('plain', 'plain'), ('markdown', 'markdown'), ('restructuredtext', 'restructuredtext')], default='restructuredtext')),
                ('_description_rendered', models.TextField(editable=False)),
                ('featured', models.BooleanField(db_index=True, default=False)),
                ('calendar', models.ForeignKey(to='events.Calendar', related_name='events', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-occurring_rule__dt_start',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('calendar', models.ForeignKey(null=True, to='events.Calendar', related_name='categories', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'event categories',
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='EventLocation',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255, blank=True, null=True)),
                ('url', models.URLField(verbose_name='URL', blank=True, null=True)),
                ('calendar', models.ForeignKey(null=True, to='events.Calendar', related_name='locations', blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OccurringRule',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('dt_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('dt_end', models.DateTimeField(default=django.utils.timezone.now)),
                ('event', models.OneToOneField(to='events.Event', related_name='occurring_rule', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(events.models.RuleMixin, models.Model),
        ),
        migrations.CreateModel(
            name='RecurringRule',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateTimeField(default=django.utils.timezone.now)),
                ('finish', models.DateTimeField(default=django.utils.timezone.now)),
                ('duration', models.CharField(max_length=50, default='15 min')),
                ('interval', models.PositiveSmallIntegerField(default=1)),
                ('frequency', models.PositiveSmallIntegerField(verbose_name=((0, 'year(s)'), (1, 'month(s)'), (2, 'week(s)'), (3, 'day(s)')), default=2)),
                ('event', models.ForeignKey(to='events.Event', related_name='recurring_rules', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(events.models.RuleMixin, models.Model),
        ),
        migrations.AddField(
            model_name='event',
            name='categories',
            field=models.ManyToManyField(null=True, to='events.EventCategory', related_name='events', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='creator',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='events_event_creator', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='last_modified_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='events_event_modified', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='venue',
            field=models.ForeignKey(null=True, to='events.EventLocation', related_name='events', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alarm',
            name='event',
            field=models.ForeignKey(to='events.Event', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='alarm',
            name='last_modified_by',
            field=models.ForeignKey(null=True, to=settings.AUTH_USER_MODEL, related_name='events_alarm_modified', blank=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
