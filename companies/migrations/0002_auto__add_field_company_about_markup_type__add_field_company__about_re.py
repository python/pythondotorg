# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Company.about_markup_type'
        db.add_column('companies_company', 'about_markup_type',
                      self.gf('django.db.models.fields.CharField')(max_length=30, default='restructuredtext', blank=True),
                      keep_default=False)

        # Adding field 'Company._about_rendered'
        db.add_column('companies_company', '_about_rendered',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)


        # Changing field 'Company.about'
        db.alter_column('companies_company', 'about', self.gf('markupfield.fields.MarkupField')(default='', rendered_field=True))

    def backwards(self, orm):
        # Deleting field 'Company.about_markup_type'
        db.delete_column('companies_company', 'about_markup_type')

        # Deleting field 'Company._about_rendered'
        db.delete_column('companies_company', '_about_rendered')


        # Changing field 'Company.about'
        db.alter_column('companies_company', 'about', self.gf('django.db.models.fields.TextField')(null=True))

    models = {
        'companies.company': {
            'Meta': {'object_name': 'Company'},
            '_about_rendered': ('django.db.models.fields.TextField', [], {}),
            'about': ('markupfield.fields.MarkupField', [], {'rendered_field': 'True', 'blank': 'True'}),
            'about_markup_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'default': "'restructuredtext'", 'blank': 'True'}),
            'contact': ('django.db.models.fields.CharField', [], {'null': 'True', 'max_length': '100', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'null': 'True', 'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'unique': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'null': 'True', 'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['companies']
