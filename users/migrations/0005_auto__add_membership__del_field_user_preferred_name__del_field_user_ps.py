# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Membership'
        db.create_table('users_membership', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('legal_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('preferred_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('email_address', self.gf('django.db.models.fields.EmailField')(max_length=100)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=20, blank=True)),
            ('psf_code_of_conduct', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('psf_announcements', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, null=True, to=orm['users.User'])),
        ))
        db.send_create_signal('users', ['Membership'])

        # Deleting field 'User.preferred_name'
        db.delete_column('users_user', 'preferred_name')

        # Deleting field 'User.psf_code_of_conduct'
        db.delete_column('users_user', 'psf_code_of_conduct')

        # Deleting field 'User.postal_code'
        db.delete_column('users_user', 'postal_code')

        # Deleting field 'User.region'
        db.delete_column('users_user', 'region')

        # Deleting field 'User.legal_name'
        db.delete_column('users_user', 'legal_name')

        # Deleting field 'User.psf_announcements'
        db.delete_column('users_user', 'psf_announcements')

        # Deleting field 'User.city'
        db.delete_column('users_user', 'city')

        # Deleting field 'User.country'
        db.delete_column('users_user', 'country')


    def backwards(self, orm):
        # Deleting model 'Membership'
        db.delete_table('users_membership')

        # Adding field 'User.preferred_name'
        db.add_column('users_user', 'preferred_name',
                      self.gf('django.db.models.fields.CharField')(max_length=100, default='', blank=True),
                      keep_default=False)

        # Adding field 'User.psf_code_of_conduct'
        db.add_column('users_user', 'psf_code_of_conduct',
                      self.gf('django.db.models.fields.NullBooleanField')(blank=True, null=True),
                      keep_default=False)

        # Adding field 'User.postal_code'
        db.add_column('users_user', 'postal_code',
                      self.gf('django.db.models.fields.CharField')(max_length=20, default='', blank=True),
                      keep_default=False)

        # Adding field 'User.region'
        db.add_column('users_user', 'region',
                      self.gf('django.db.models.fields.CharField')(max_length=100, default='', blank=True),
                      keep_default=False)

        # Adding field 'User.legal_name'
        db.add_column('users_user', 'legal_name',
                      self.gf('django.db.models.fields.CharField')(max_length=100, default='', blank=True),
                      keep_default=False)

        # Adding field 'User.psf_announcements'
        db.add_column('users_user', 'psf_announcements',
                      self.gf('django.db.models.fields.NullBooleanField')(blank=True, null=True),
                      keep_default=False)

        # Adding field 'User.city'
        db.add_column('users_user', 'city',
                      self.gf('django.db.models.fields.CharField')(max_length=100, default='', blank=True),
                      keep_default=False)

        # Adding field 'User.country'
        db.add_column('users_user', 'country',
                      self.gf('django.db.models.fields.CharField')(max_length=100, default='', blank=True),
                      keep_default=False)


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'object_name': 'ContentType', 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'users.membership': {
            'Meta': {'object_name': 'Membership'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['users.User']"}),
            'email_address': ('django.db.models.fields.EmailField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'legal_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'preferred_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'psf_announcements': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'psf_code_of_conduct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            '_bio_rendered': ('django.db.models.fields.TextField', [], {}),
            'bio': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True', 'blank': 'True'}),
            'bio_markup_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'default': "'markdown'", 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'email_privacy': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'search_visibility': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        }
    }

    complete_apps = ['users']