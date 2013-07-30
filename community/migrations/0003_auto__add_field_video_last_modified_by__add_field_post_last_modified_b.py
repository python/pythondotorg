# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Video.last_modified_by'
        db.add_column('community_video', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['users.User'], null=True, related_name='community_video_modified'),
                      keep_default=False)

        # Adding field 'Post.last_modified_by'
        db.add_column('community_post', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['users.User'], null=True, related_name='community_post_modified'),
                      keep_default=False)

        # Adding field 'Link.last_modified_by'
        db.add_column('community_link', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['users.User'], null=True, related_name='community_link_modified'),
                      keep_default=False)

        # Adding field 'Photo.last_modified_by'
        db.add_column('community_photo', 'last_modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, to=orm['users.User'], null=True, related_name='community_photo_modified'),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Video.last_modified_by'
        db.delete_column('community_video', 'last_modified_by_id')

        # Deleting field 'Post.last_modified_by'
        db.delete_column('community_post', 'last_modified_by_id')

        # Deleting field 'Link.last_modified_by'
        db.delete_column('community_link', 'last_modified_by_id')

        # Deleting field 'Photo.last_modified_by'
        db.delete_column('community_photo', 'last_modified_by_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'to': "orm['auth.Permission']", 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'community.link': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Link'},
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_link_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_link_modified'"}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['community.Post']", 'related_name': "'related_link'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '1000'})
        },
        'community.photo': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Photo'},
            'caption': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'click_through_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_photo_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'blank': 'True', 'max_length': '100'}),
            'image_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '1000'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_photo_modified'"}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['community.Post']", 'related_name': "'related_photo'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'community.post': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Post'},
            '_content_rendered': ('django.db.models.fields.TextField', [], {}),
            'abstract': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'content': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True'}),
            'content_markup_type': ('django.db.models.fields.CharField', [], {'default': "'html'", 'max_length': '30'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_post_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_post_modified'"}),
            'media_type': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'meta': ('jsonfield.fields.JSONField', [], {'blank': 'True', 'default': '{}'}),
            'source_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '1000'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'blank': 'True', 'null': 'True', 'max_length': '200'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'community.video': {
            'Meta': {'ordering': "['-created']", 'object_name': 'Video'},
            'caption': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'click_through_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_video_creator'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'to': "orm['users.User']", 'null': 'True', 'related_name': "'community_video_modified'"}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'to': "orm['community.Post']", 'related_name': "'related_video'"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'video_data': ('django.db.models.fields.files.FileField', [], {'blank': 'True', 'max_length': '100'}),
            'video_embed': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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

    complete_apps = ['community']