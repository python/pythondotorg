# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import apps as global_apps
from django.contrib.contenttypes.management import update_contenttypes
from django.db import models, migrations
from django.utils.timezone import now

MARKER = '.. Migrated from django_comments_xtd.Comment model.\n\n'

comments_app_name = 'django_comments_xtd'
content_type = 'job'


def migrate_old_content(apps, schema_editor):
    try:
        Comment = apps.get_model(comments_app_name, 'XtdComment')
    except LookupError:
        # django_comments_xtd isn't installed.
        return
    update_contenttypes(apps.app_configs['contenttypes'])
    JobReviewComment = apps.get_model('jobs', 'JobReviewComment')
    Job = apps.get_model('jobs', 'Job')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    db_alias = schema_editor.connection.alias
    try:
        # 'ContentType.name' is now a property in Django 1.8 so we
        # can't use it to query a ContentType anymore.
        job_contenttype = ContentType.objects.using(db_alias).get(model=content_type)
    except ContentType.DoesNotExist:
        return
    old_comments = Comment.objects.using(db_alias).filter(
        content_type=job_contenttype.pk, is_public=True, is_removed=False,
    )
    found_jobs = {}
    comments = []
    for comment in old_comments:
        try:
            job = found_jobs[comment.object_pk]
        except KeyError:
            try:
                job = Job.objects.using(db_alias).get(pk=comment.object_pk)
                found_jobs[comment.object_pk] = job
            except Job.DoesNotExist:
                continue
        review_comment = JobReviewComment(
            job=job,
            comment=MARKER + comment.comment,
            creator=comment.user,
            created=comment.submit_date,
            updated=now(),
        )
        comments.append(review_comment)
    JobReviewComment.objects.using(db_alias).bulk_create(comments)


def delete_migrated_content(apps, schema_editor):
    JobReviewComment = apps.get_model('jobs', 'JobReviewComment')
    db_alias = schema_editor.connection.alias
    JobReviewComment.objects.using(db_alias).filter(comment__startswith=MARKER).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('jobs', '0011_jobreviewcomment'),
    ]
    if global_apps.is_installed(comments_app_name):
        dependencies.append((comments_app_name, '0001_initial'))

    operations = [
        migrations.RunPython(migrate_old_content, delete_migrated_content),
    ]
