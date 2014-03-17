# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Job.company_name'
        db.add_column('jobs_job', 'company_name',
                      self.gf('django.db.models.fields.CharField')(null=True, blank=True, max_length=100),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Job.company_name'
        db.delete_column('jobs_job', 'company_name')


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
        'companies.company': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Company'},
            '_about_rendered': ('django.db.models.fields.TextField', [], {}),
            'about': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'about_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30', 'default': "'restructuredtext'"}),
            'contact': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'blank': 'True', 'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'})
        },
        'contenttypes.contenttype': {
            'Meta': {'db_table': "'django_content_type'", 'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType'},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'jobs.job': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Job'},
            '_description_rendered': ('django.db.models.fields.TextField', [], {}),
            '_requirements_rendered': ('django.db.models.fields.TextField', [], {}),
            'agencies': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['jobs.JobCategory']"}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['companies.Company']", 'null': 'True', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'contact': ('django.db.models.fields.CharField', [], {'null': 'True', 'blank': 'True', 'max_length': '100'}),
            'country': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs_job_creator'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'description': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'description_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30', 'default': "'restructuredtext'"}),
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_featured': ('django.db.models.fields.BooleanField', [], {'db_index': 'True', 'default': 'False'}),
            'job_types': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'jobs'", 'to': "orm['jobs.JobType']", 'blank': 'True', 'symmetrical': 'False'}),
            'last_modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs_job_modified'", 'to': "orm['users.User']", 'null': 'True', 'blank': 'True'}),
            'location_slug': ('django.db.models.fields.SlugField', [], {'max_length': '350'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'requirements': ('markupfield.fields.MarkupField', [], {'blank': 'True', 'rendered_field': 'True'}),
            'requirements_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30', 'default': "'restructuredtext'"}),
            'status': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '20', 'default': "'draft'"}),
            'telecommuting': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'null': 'True', 'blank': 'True', 'max_length': '200'})
        },
        'jobs.jobcategory': {
            'Meta': {'ordering': "('name',)", 'object_name': 'JobCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'jobs.jobtype': {
            'Meta': {'ordering': "('name',)", 'object_name': 'JobType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
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

    complete_apps = ['jobs']