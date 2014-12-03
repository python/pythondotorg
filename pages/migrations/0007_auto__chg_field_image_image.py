# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Image.image'
        db.alter_column('pages_image', 'image', self.gf('django.db.models.fields.files.ImageField')(max_length=400))

    def backwards(self, orm):

        # Changing field 'Image.image'
        db.alter_column('pages_image', 'image', self.gf('django.db.models.fields.files.ImageField')(max_length=100))

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
        'pages.image': {
            'Meta': {'object_name': 'Image'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '400'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pages.Page']"})
        },
        'pages.page': {
            'Meta': {'ordering': "['title', 'path']", 'object_name': 'Page'},
            '_content_rendered': ('django.db.models.fields.TextField', [], {}),
            'content': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'content_markup_type': ('django.db.models.fields.CharField', [], {'default': "'restructuredtext'", 'max_length': '30'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'related_name': "'pages_page_creator'", 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '1000'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']", 'null': 'True', 'related_name': "'pages_page_modified'", 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'db_index': 'True', 'max_length': '500'}),
            'template_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
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

    complete_apps = ['pages']