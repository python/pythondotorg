# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'OccurringRule.date_start'
        db.add_column('events_occurringrule', 'date_start',
                      self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'OccurringRule.date_end'
        db.add_column('events_occurringrule', 'date_end',
                      self.gf('django.db.models.fields.DateField')(default=datetime.datetime.now),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'OccurringRule.date_start'
        db.delete_column('events_occurringrule', 'date_start')

        # Deleting field 'OccurringRule.date_end'
        db.delete_column('events_occurringrule', 'date_end')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'object_name': 'ContentType', 'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'events.alarm': {
            'Meta': {'object_name': 'Alarm'},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_alarm_creator'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_alarm_modified'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'trigger': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '24'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'events.calendar': {
            'Meta': {'object_name': 'Calendar'},
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_calendar_creator'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_calendar_modified'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'events.event': {
            'Meta': {'object_name': 'Event'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {}),
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'to': "orm['events.Calendar']"}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'events'", 'null': 'True', 'to': "orm['events.EventCategory']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_event_creator'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'description': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'description_markup_type': ('django.db.models.fields.CharField', [], {'default': "'restructuredtext'", 'max_length': '30'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'db_index': 'True', 'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_event_modified'", 'null': 'True', 'to': "orm['users.User']", 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'uid': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'venue': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events'", 'null': 'True', 'to': "orm['events.EventLocation']", 'blank': 'True'})
        },
        'events.eventcategory': {
            'Meta': {'object_name': 'EventCategory', 'ordering': "('name',)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'events.eventlocation': {
            'Meta': {'object_name': 'EventLocation', 'ordering': "('name',)"},
            'address': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'})
        },
        'events.occurringrule': {
            'Meta': {'object_name': 'OccurringRule'},
            'date_end': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'date_start': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime.now'}),
            'datetime_end': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'datetime_start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'event': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'occurring_rule'", 'unique': 'True', 'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'events.recurringrule': {
            'Meta': {'object_name': 'RecurringRule'},
            'begin': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'duration': ('timedelta.fields.TimedeltaField', [], {'default': "'15 mins'"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recurring_rules'", 'to': "orm['events.Event']"}),
            'finish': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'frequency': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interval': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            '_bio_rendered': ('django.db.models.fields.TextField', [], {}),
            'bio': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True', 'blank': 'True'}),
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