# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import markupfield.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkGroup',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, db_index=True, blank=True)),
                ('updated', models.DateTimeField(blank=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('active', models.BooleanField(default=True, db_index=True)),
                ('approved', models.BooleanField(default=False, db_index=True)),
                ('short_description', models.TextField(help_text='Short description used on listing pages', blank=True)),
                ('purpose', markupfield.fields.MarkupField(rendered_field=True, help_text='State what the mission of the group is. List all (if any) common goals that will be shared amongst the workgroup.')),
                ('purpose_markup_type', models.CharField(default='restructuredtext', max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')])),
                ('active_time', markupfield.fields.MarkupField(rendered_field=True, help_text='How long will this workgroup exist? If the mission is not complete by the stated time, is it extendable? Is so, for how long?')),
                ('_purpose_rendered', models.TextField(editable=False)),
                ('core_values', markupfield.fields.MarkupField(rendered_field=True, help_text='List the core values that the workgroup will adhere to throughout its existence. Will the workgroup adopt any statements? If so, which statement?')),
                ('active_time_markup_type', models.CharField(default='restructuredtext', max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')])),
                ('rules', markupfield.fields.MarkupField(rendered_field=True, help_text='Give a comprehensive explanation of how the decision making will work within the workgroup and list the rules that accompany these procedures.')),
                ('core_values_markup_type', models.CharField(default='restructuredtext', max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')])),
                ('_active_time_rendered', models.TextField(editable=False)),
                ('rules_markup_type', models.CharField(default='restructuredtext', max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')])),
                ('communication', markupfield.fields.MarkupField(rendered_field=True, help_text='How will the team communicate? How often will the team communicate?')),
                ('_core_values_rendered', models.TextField(editable=False)),
                ('_rules_rendered', models.TextField(editable=False)),
                ('communication_markup_type', models.CharField(default='restructuredtext', max_length=30, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')])),
                ('support', markupfield.fields.MarkupField(rendered_field=True, help_text='What resources will you need from the PSF in order to have a functional and effective workgroup?', blank=True)),
                ('_communication_rendered', models.TextField(editable=False)),
                ('support_markup_type', models.CharField(default='restructuredtext', max_length=30, blank=True, choices=[('', '--'), ('html', 'HTML'), ('plain', 'Plain'), ('markdown', 'Markdown'), ('restructuredtext', 'Restructured Text')])),
                ('url', models.URLField(help_text='Main URL for Group', blank=True)),
                ('_support_rendered', models.TextField(editable=False)),
                ('creator', models.ForeignKey(blank=True, related_name='work_groups_workgroup_creator', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(blank=True, related_name='work_groups_workgroup_modified', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('members', models.ManyToManyField(related_name='working_groups', to=settings.AUTH_USER_MODEL)),
                ('organizers', models.ManyToManyField(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
