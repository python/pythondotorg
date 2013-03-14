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
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('jobs', ['JobType'])

        # Adding model 'JobCategory'
        db.create_table('jobs_jobcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('jobs', ['JobCategory'])

        # Adding model 'Job'
        db.create_table('jobs_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['users.User'], blank=True, null=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', to=orm['jobs.JobCategory'])),
            ('company', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', to=orm['companies.Company'])),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('region', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('location_slug', self.gf('django.db.models.fields.SlugField')(max_length=350)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('requirements', self.gf('markupfield.fields.MarkupField')(rendered_field=True, blank=True)),
            ('requirements_markup_type', self.gf('django.db.models.fields.CharField')(default='restructuredtext', blank=True, max_length=30)),
            ('contact', self.gf('django.db.models.fields.CharField')(blank=True, max_length=100, null=True)),
            ('_requirements_rendered', self.gf('django.db.models.fields.TextField')()),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('url', self.gf('django.db.models.fields.URLField')(blank=True, max_length=200, null=True)),
            ('telecommuting', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('agencies', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('jobs', ['Job'])

        # Adding M2M table for field job_types on 'Job'
        m2m_table_name = db.shorten_name('jobs_job_job_types')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('job', models.ForeignKey(orm['jobs.job'], null=False)),
            ('jobtype', models.ForeignKey(orm['jobs.jobtype'], null=False))
        ))
        db.create_unique(m2m_table_name, ['job_id', 'jobtype_id'])


    def backwards(self, orm):
        # Deleting model 'JobType'
        db.delete_table('jobs_jobtype')

        # Deleting model 'JobCategory'
        db.delete_table('jobs_jobcategory')

        # Deleting model 'Job'
        db.delete_table('jobs_job')

        # Removing M2M table for field job_types on 'Job'
        db.delete_table(db.shorten_name('jobs_job_job_types'))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission', 'ordering': "('content_type__app_label', 'content_type__model', 'codename')"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'companies.company': {
            'Meta': {'object_name': 'Company'},
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'contact': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'", 'ordering': "('name',)"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'jobs.job': {
            'Meta': {'object_name': 'Job', 'ordering': "('-created',)"},
            '_requirements_rendered': ('django.db.models.fields.TextField', [], {}),
            'agencies': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['jobs.JobCategory']"}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'company': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'to': "orm['companies.Company']"}),
            'contact': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['users.User']", 'blank': 'True', 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'jobs'", 'to': "orm['jobs.JobType']"}),
            'location_slug': ('django.db.models.fields.SlugField', [], {'max_length': '350'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'requirements': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True', 'blank': 'True'}),
            'requirements_markup_type': ('django.db.models.fields.CharField', [], {'default': "'restructuredtext'", 'blank': 'True', 'max_length': '30'}),
            'telecommuting': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'})
        },
        'jobs.jobcategory': {
            'Meta': {'object_name': 'JobCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'jobs.jobtype': {
            'Meta': {'object_name': 'JobType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_beta_tester': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '30'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['jobs']