# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ReleaseFile.download_button'
        db.add_column('downloads_releasefile', 'download_button',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'ReleaseFile.download_button'
        db.delete_column('downloads_releasefile', 'download_button')


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
            'Meta': {'db_table': "'django_content_type'", 'object_name': 'ContentType', 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'downloads.os': {
            'Meta': {'object_name': 'OS', 'ordering': "('name',)"},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'db_index': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'downloads_os_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'downloads_os_modified'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'downloads.release': {
            'Meta': {'object_name': 'Release', 'ordering': "('name',)"},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'db_index': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'downloads_release_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'db_index': 'True', 'default': 'False'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'downloads_release_modified'"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'release_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'release_notes_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200'}),
            'release_page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pages.Page']", 'related_name': "'release'"}),
            'show_on_download_page': ('django.db.models.fields.BooleanField', [], {'db_index': 'True', 'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': '2'})
        },
        'downloads.releasefile': {
            'Meta': {'object_name': 'ReleaseFile', 'ordering': "('-release__is_published', 'release__name', 'os__name')"},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'db_index': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'downloads_releasefile_creator'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'download_button': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'filesize': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_source': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'downloads_releasefile_modified'"}),
            'md5_sum': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'os': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['downloads.OS']", 'related_name': "'releases'"}),
            'release': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['downloads.Release']", 'related_name': "'files'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'unique': 'True', 'db_index': 'True'})
        },
        'pages.page': {
            'Meta': {'object_name': 'Page', 'ordering': "['title', 'path']"},
            '_content_rendered': ('django.db.models.fields.TextField', [], {}),
            'content': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'content_markup_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'default': "'restructuredtext'"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'db_index': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'pages_page_creator'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_published': ('django.db.models.fields.BooleanField', [], {'db_index': 'True', 'default': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '1000'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'blank': 'True', 'to': "orm['users.User']", 'related_name': "'pages_page_modified'"}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '500', 'unique': 'True', 'db_index': 'True'}),
            'template_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            '_bio_rendered': ('django.db.models.fields.TextField', [], {}),
            'bio': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'bio_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30', 'default': "'markdown'"}),
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

    complete_apps = ['downloads']
