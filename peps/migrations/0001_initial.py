# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PepType'
        db.create_table('peps_peptype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, blank=True)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('peps', ['PepType'])

        # Adding model 'PepStatus'
        db.create_table('peps_pepstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, blank=True)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('peps', ['PepStatus'])

        # Adding model 'PepOwner'
        db.create_table('peps_pepowner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('email', self.gf('django.db.models.fields.EmailField')(blank=True, max_length=75)),
        ))
        db.send_create_signal('peps', ['PepOwner'])

        # Adding model 'PepCategory'
        db.create_table('peps_pepcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('peps', ['PepCategory'])

        # Adding model 'Pep'
        db.create_table('peps_pep', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.User'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['peps.PepType'], related_name='peps')),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['peps.PepStatus'], related_name='peps')),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['peps.PepCategory'], related_name='peps')),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('number', self.gf('django.db.models.fields.IntegerField')()),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255)),
        ))
        db.send_create_signal('peps', ['Pep'])

        # Adding M2M table for field owners on 'Pep'
        m2m_table_name = db.shorten_name('peps_pep_owners')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pep', models.ForeignKey(orm['peps.pep'], null=False)),
            ('pepowner', models.ForeignKey(orm['peps.pepowner'], null=False))
        ))
        db.create_unique(m2m_table_name, ['pep_id', 'pepowner_id'])


    def backwards(self, orm):
        # Deleting model 'PepType'
        db.delete_table('peps_peptype')

        # Deleting model 'PepStatus'
        db.delete_table('peps_pepstatus')

        # Deleting model 'PepOwner'
        db.delete_table('peps_pepowner')

        # Deleting model 'PepCategory'
        db.delete_table('peps_pepcategory')

        # Deleting model 'Pep'
        db.delete_table('peps_pep')

        # Removing M2M table for field owners on 'Pep'
        db.delete_table(db.shorten_name('peps_pep_owners'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'unique_together': "(('app_label', 'model'),)", 'ordering': "('name',)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'peps.pep': {
            'Meta': {'object_name': 'Pep'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['peps.PepCategory']", 'related_name': "'peps'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['peps.PepOwner']", 'symmetrical': 'False', 'related_name': "'peps'"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['peps.PepStatus']", 'related_name': "'peps'"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['peps.PepType']", 'related_name': "'peps'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255'})
        },
        'peps.pepcategory': {
            'Meta': {'object_name': 'PepCategory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'peps.pepowner': {
            'Meta': {'object_name': 'PepOwner'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'peps.pepstatus': {
            'Meta': {'object_name': 'PepStatus'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'peps.peptype': {
            'Meta': {'object_name': 'PepType'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'search_visibility': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['peps']
