# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Calendar'
        db.create_table('events_calendar', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', to=orm['auth.User'], null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('events', ['Calendar'])

        # Adding model 'EventCategory'
        db.create_table('events_eventcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('events', ['EventCategory'])

        # Adding model 'EventLocation'
        db.create_table('events_eventlocation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('address', self.gf('django.db.models.fields.CharField')(blank=True, max_length=255, null=True)),
            ('url', self.gf('django.db.models.fields.URLField')(blank=True, max_length=200, null=True)),
        ))
        db.send_create_signal('events', ['EventLocation'])

        # Adding model 'Event'
        db.create_table('events_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', to=orm['auth.User'], null=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('calendar', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['events.Calendar'], related_name='events')),
            ('description', self.gf('markupfield.fields.MarkupField')(rendered_field=True)),
            ('venue', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='events', to=orm['events.EventLocation'], null=True)),
            ('description_markup_type', self.gf('django.db.models.fields.CharField')(max_length=30, default='restructuredtext')),
            ('_description_rendered', self.gf('django.db.models.fields.TextField')()),
            ('featured', self.gf('django.db.models.fields.BooleanField')(db_index=True, default=False)),
        ))
        db.send_create_signal('events', ['Event'])

        # Adding M2M table for field categories on 'Event'
        db.create_table('events_event_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('event', models.ForeignKey(orm['events.event'], null=False)),
            ('eventcategory', models.ForeignKey(orm['events.eventcategory'], null=False))
        ))
        db.create_unique('events_event_categories', ['event_id', 'eventcategory_id'])

        # Adding model 'OccurringRule'
        db.create_table('events_occurringrule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['events.Event'], unique=True, related_name='occurring_rule')),
            ('dt_start', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('dt_end', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('events', ['OccurringRule'])

        # Adding model 'RecurringRule'
        db.create_table('events_recurringrule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['events.Event'], related_name='recurring_rules')),
            ('begin', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('finish', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('duration', self.gf('timedelta.fields.TimedeltaField')(default='15 mins')),
            ('interval', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('frequency', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=2)),
        ))
        db.send_create_signal('events', ['RecurringRule'])

        # Adding model 'Alarm'
        db.create_table('events_alarm', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', to=orm['auth.User'], null=True)),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['events.Event'])),
            ('trigger', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=24)),
        ))
        db.send_create_signal('events', ['Alarm'])


    def backwards(self, orm):
        # Deleting model 'Calendar'
        db.delete_table('events_calendar')

        # Deleting model 'EventCategory'
        db.delete_table('events_eventcategory')

        # Deleting model 'EventLocation'
        db.delete_table('events_eventlocation')

        # Deleting model 'Event'
        db.delete_table('events_event')

        # Removing M2M table for field categories on 'Event'
        db.delete_table('events_event_categories')

        # Deleting model 'OccurringRule'
        db.delete_table('events_occurringrule')

        # Deleting model 'RecurringRule'
        db.delete_table('events_recurringrule')

        # Deleting model 'Alarm'
        db.delete_table('events_alarm')


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
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Group']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'events.alarm': {
            'Meta': {'object_name': 'Alarm'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'to': "orm['auth.User']", 'null': 'True'}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'trigger': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '24'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'events.calendar': {
            'Meta': {'object_name': 'Calendar'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'to': "orm['auth.User']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'events.event': {
            'Meta': {'object_name': 'Event'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {}),
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Calendar']", 'related_name': "'events'"}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'events'", 'to': "orm['events.EventCategory']", 'null': 'True', 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'to': "orm['auth.User']", 'null': 'True'}),
            'description': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'description_markup_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'default': "'restructuredtext'"}),
            'featured': ('django.db.models.fields.BooleanField', [], {'db_index': 'True', 'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'venue': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'events'", 'to': "orm['events.EventLocation']", 'null': 'True'})
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
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'event': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['events.Event']", 'unique': 'True', 'related_name': "'occurring_rule'"}),
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
        }
    }

    complete_apps = ['events']