# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Company'
        db.create_table('companies_company', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, unique=True)),
            ('about', self.gf('django.db.models.fields.TextField')(blank=True, null=True)),
            ('contact', self.gf('django.db.models.fields.CharField')(blank=True, max_length=100, null=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(blank=True, max_length=75, null=True)),
            ('url', self.gf('django.db.models.fields.URLField')(blank=True, max_length=200, null=True)),
        ))
        db.send_create_signal('companies', ['Company'])


    def backwards(self, orm):
        # Deleting model 'Company'
        db.delete_table('companies_company')


    models = {
        'companies.company': {
            'Meta': {'object_name': 'Company'},
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True', 'null': 'True'}),
            'contact': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'})
        }
    }

    complete_apps = ['companies']