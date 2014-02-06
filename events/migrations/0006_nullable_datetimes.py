# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'OccurringRule.date_start'
        db.alter_column('events_occurringrule', 'date_start', self.gf('django.db.models.fields.DateField')(null=True))

        # Changing field 'OccurringRule.datetime_start'
        db.alter_column('events_occurringrule', 'datetime_start', self.gf('django.db.models.fields.DateTimeField')(null=True))

        # Changing field 'OccurringRule.date_end'
        db.alter_column('events_occurringrule', 'date_end', self.gf('django.db.models.fields.DateField')(null=True))

        # Changing field 'OccurringRule.datetime_end'
        db.alter_column('events_occurringrule', 'datetime_end', self.gf('django.db.models.fields.DateTimeField')(null=True))

    def backwards(self, orm):

        # Changing field 'OccurringRule.date_start'
        db.alter_column('events_occurringrule', 'date_start', self.gf('django.db.models.fields.DateField')())

        # Changing field 'OccurringRule.datetime_start'
        db.alter_column('events_occurringrule', 'datetime_start', self.gf('django.db.models.fields.DateTimeField')())

        # Changing field 'OccurringRule.date_end'
        db.alter_column('events_occurringrule', 'date_end', self.gf('django.db.models.fields.DateField')())

        # Changing field 'OccurringRule.datetime_end'
        db.alter_column('events_occurringrule', 'datetime_end', self.gf('django.db.models.fields.DateTimeField')())

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'object_name': 'ContentType', 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'events.alarm': {
            'Meta': {'object_name': 'Alarm'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'events_alarm_creator'", 'null': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'events_alarm_modified'", 'null': 'True'}),
            'trigger': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '24'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'events.calendar': {
            'Meta': {'object_name': 'Calendar'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'events_calendar_creator'", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'events_calendar_modified'", 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'events.event': {
            'Meta': {'object_name': 'Event'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {}),
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Calendar']", 'related_name': "'events'"}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['events.EventCategory']", 'symmetrical': 'False', 'related_name': "'events'", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'events_event_creator'", 'null': 'True'}),
            'description': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'description_markup_type': ('django.db.models.fields.CharField', [], {'default': "'restructuredtext'", 'max_length': '30'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'related_name': "'events_event_modified'", 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uid': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'venue': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['events.EventLocation']", 'related_name': "'events'", 'null': 'True'})
        },
        'events.eventcategory': {
            'Meta': {'object_name': 'EventCategory', 'ordering': "('name',)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'events.eventlocation': {
            'Meta': {'object_name': 'EventLocation', 'ordering': "('name',)"},
            'address': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '255', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'})
        },
        'events.occurringrule': {
            'Meta': {'object_name': 'OccurringRule'},
            'date_end': ('django.db.models.fields.DateField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'null': 'True'}),
            'date_start': ('django.db.models.fields.DateField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'null': 'True'}),
            'datetime_end': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'null': 'True'}),
            'datetime_start': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'null': 'True'}),
            'event': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['events.Event']", 'related_name': "'occurring_rule'", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'events.recurringrule': {
            'Meta': {'object_name': 'RecurringRule'},
            'begin': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'duration': ('timedelta.fields.TimedeltaField', [], {'default': "'15 mins'"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']", 'related_name': "'recurring_rules'"}),
            'finish': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'frequency': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            '_bio_rendered': ('django.db.models.fields.TextField', [], {}),
            'bio': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'bio_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'markdown'", 'max_length': '30'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'email_privacy': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'search_visibility': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['events']