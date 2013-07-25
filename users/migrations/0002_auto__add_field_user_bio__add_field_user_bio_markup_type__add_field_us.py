# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.bio'
        db.add_column('users_user', 'bio',
                      self.gf('markupfield.fields.MarkupField')(default='', blank=True, rendered_field=True),
                      keep_default=False)

        # Adding field 'User.bio_markup_type'
        db.add_column('users_user', 'bio_markup_type',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='markdown', max_length=30),
                      keep_default=False)

        # Adding field 'User.city'
        db.add_column('users_user', 'city',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=100),
                      keep_default=False)

        # Adding field 'User._bio_rendered'
        db.add_column('users_user', '_bio_rendered',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'User.region'
        db.add_column('users_user', 'region',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=100),
                      keep_default=False)

        # Adding field 'User.country'
        db.add_column('users_user', 'country',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=100),
                      keep_default=False)

        # Adding field 'User.postal_code'
        db.add_column('users_user', 'postal_code',
                      self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=20),
                      keep_default=False)

        # Adding field 'User.psf_code_of_conduct'
        db.add_column('users_user', 'psf_code_of_conduct',
                      self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'User.psf_announcements'
        db.add_column('users_user', 'psf_announcements',
                      self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.bio'
        db.delete_column('users_user', 'bio')

        # Deleting field 'User.bio_markup_type'
        db.delete_column('users_user', 'bio_markup_type')

        # Deleting field 'User.city'
        db.delete_column('users_user', 'city')

        # Deleting field 'User._bio_rendered'
        db.delete_column('users_user', '_bio_rendered')

        # Deleting field 'User.region'
        db.delete_column('users_user', 'region')

        # Deleting field 'User.country'
        db.delete_column('users_user', 'country')

        # Deleting field 'User.postal_code'
        db.delete_column('users_user', 'postal_code')

        # Deleting field 'User.psf_code_of_conduct'
        db.delete_column('users_user', 'psf_code_of_conduct')

        # Deleting field 'User.psf_announcements'
        db.delete_column('users_user', 'psf_announcements')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            '_bio_rendered': ('django.db.models.fields.TextField', [], {}),
            'bio': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'bio_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'markdown'", 'max_length': '30'}),
            'city': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100'}),
            'country': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True', 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '20'}),
            'psf_announcements': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'psf_code_of_conduct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True', 'symmetrical': 'False'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['users']