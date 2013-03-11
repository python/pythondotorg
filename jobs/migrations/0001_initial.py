# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'JobType'
        db.create_table('jobs_jobtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True)),
        ))
        db.send_create_signal('jobs', ['JobType'])

        # Adding model 'JobCategory'
        db.create_table('jobs_jobcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True)),
        ))
        db.send_create_signal('jobs', ['JobCategory'])

        # Adding model 'Job'
        db.create_table('jobs_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', to=orm['auth.User'], null=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', to=orm['jobs.JobCategory'])),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', to=orm['companies.Company'])),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('location_slug', self.gf('django.db.models.fields.SlugField')(max_length=350)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('requirements', self.gf('markupfield.fields.MarkupField')(rendered_field=True, blank=True)),
            ('requirements_markup_type', self.gf('django.db.models.fields.CharField')(blank=True, default='restructuredtext', max_length=30)),
            ('contact', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True, null=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('_requirements_rendered', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True, null=True)),
            ('telecommuting', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('agencies', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('jobs', ['Job'])

        # Adding M2M table for field job_types on 'Job'
        db.create_table('jobs_job_job_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('job', models.ForeignKey(orm['jobs.job'], null=False)),
            ('jobtype', models.ForeignKey(orm['jobs.jobtype'], null=False))
        ))
        db.create_unique('jobs_job_job_types', ['job_id', 'jobtype_id'])


    def backwards(self, orm):
        # Deleting model 'JobType'
        db.delete_table('jobs_jobtype')

        # Deleting model 'JobCategory'
        db.delete_table('jobs_jobcategory')

        # Deleting model 'Job'
        db.delete_table('jobs_job')

        # Removing M2M table for field job_types on 'Job'
        db.delete_table('jobs_job_job_types')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Permission']"})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'symmetrical': 'False', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'companies.company': {
            'Meta': {'object_name': 'Company'},
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'contact': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True', 'null': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'jobs.job': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Job'},
            '_requirements_rendered': ('django.db.models.fields.TextField', [], {}),
            'agencies': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['jobs.JobCategory']"}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['companies.Company']"}),
            'contact': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True', 'null': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'to': "orm['auth.User']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['jobs.JobType']", 'related_name': "'jobs'"}),
            'location_slug': ('django.db.models.fields.SlugField', [], {'max_length': '350'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'requirements': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True', 'blank': 'True'}),
            'requirements_markup_type': ('django.db.models.fields.CharField', [], {'blank': 'True', 'default': "'restructuredtext'", 'max_length': '30'}),
            'telecommuting': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True', 'null': 'True'})
        },
        'jobs.jobcategory': {
            'Meta': {'object_name': 'JobCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True'})
        },
        'jobs.jobtype': {
            'Meta': {'object_name': 'JobType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True'})
        }
    }

    complete_apps = ['jobs']