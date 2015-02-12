# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, blank=True, null=True)),
                ('email', models.EmailField(max_length=75, blank=True, null=True)),
                ('country', models.CharField(max_length=100, blank=True, null=True)),
                ('referral_url', models.URLField(blank=True, null=True)),
                ('is_beta_tester', models.BooleanField(default=False)),
                ('comment', models.TextField()),
                ('created', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
            ],
            options={
                'verbose_name': 'feedback',
                'verbose_name_plural': 'feedbacks',
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FeedbackCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'feedback category',
                'verbose_name_plural': 'feedback categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssueType',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
            ],
            options={
                'verbose_name': 'issue type',
                'verbose_name_plural': 'issue types',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='feedback',
            name='feedback_categories',
            field=models.ManyToManyField(null=True, to='feedbacks.FeedbackCategory', related_name='feedbacks', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='feedback',
            name='issue_type',
            field=models.ForeignKey(null=True, to='feedbacks.IssueType', related_name='feedbacks', blank=True),
            preserve_default=True,
        ),
    ]
