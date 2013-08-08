# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Pep.last_modified_by'
        db.add_column('peps_pep', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['users.User'], blank=True, related_name='peps_pep_modified'),
                      keep_default=False)

        # Adding field 'PepOwner.last_modified_by'
        db.add_column('peps_pepowner', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['users.User'], blank=True, related_name='peps_pepowner_modified'),
                      keep_default=False)

        # Adding field 'PepCategory.last_modified_by'
        db.add_column('peps_pepcategory', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['users.User'], blank=True, related_name='peps_pepcategory_modified'),
                      keep_default=False)

        # Adding field 'PepType.last_modified_by'
        db.add_column('peps_peptype', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['users.User'], blank=True, related_name='peps_peptype_modified'),
                      keep_default=False)

        # Adding field 'PepStatus.last_modified_by'
        db.add_column('peps_pepstatus', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['users.User'], blank=True, related_name='peps_pepstatus_modified'),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Pep.last_modified_by'
        db.delete_column('peps_pep', 'last_modified_by_id')

        # Deleting field 'PepOwner.last_modified_by'
        db.delete_column('peps_pepowner', 'last_modified_by_id')

        # Deleting field 'PepCategory.last_modified_by'
        db.delete_column('peps_pepcategory', 'last_modified_by_id')

        # Deleting field 'PepType.last_modified_by'
        db.delete_column('peps_peptype', 'last_modified_by_id')

        # Deleting field 'PepStatus.last_modified_by'
        db.delete_column('peps_pepstatus', 'last_modified_by_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
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
        'peps.pep': {
            'Meta': {'object_name': 'Pep'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['peps.PepCategory']", 'related_name': "'peps'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pep_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pep_modified'"}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['peps.PepOwner']", 'related_name': "'peps'"}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['peps.PepStatus']", 'blank': 'True', 'related_name': "'peps'"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['peps.PepType']", 'related_name': "'peps'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255'})
        },
        'peps.pepcategory': {
            'Meta': {'object_name': 'PepCategory'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pepcategory_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pepcategory_modified'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'peps.pepowner': {
            'Meta': {'object_name': 'PepOwner'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pepowner_creator'"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pepowner_modified'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'peps.pepstatus': {
            'Meta': {'object_name': 'PepStatus'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pepstatus_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_pepstatus_modified'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'peps.peptype': {
            'Meta': {'object_name': 'PepType'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_peptype_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['users.User']", 'blank': 'True', 'related_name': "'peps_peptype_modified'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            '_bio_rendered': ('django.db.models.fields.TextField', [], {}),
            'bio': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'bio_markup_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'default': "'markdown'", 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'email_privacy': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'search_visibility': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['peps']