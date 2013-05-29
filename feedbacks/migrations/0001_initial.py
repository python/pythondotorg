# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FeedbackCategory'
        db.create_table('feedbacks_feedbackcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('feedbacks', ['FeedbackCategory'])

        # Adding model 'IssueType'
        db.create_table('feedbacks_issuetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('feedbacks', ['IssueType'])

        # Adding model 'Feedback'
        db.create_table('feedbacks_feedback', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(blank=True, max_length=200, null=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(blank=True, max_length=75, null=True)),
            ('country', self.gf('django.db.models.fields.CharField')(blank=True, max_length=100, null=True)),
            ('issue_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, null=True, to=orm['feedbacks.IssueType'], related_name='feedbacks')),
            ('referral_url', self.gf('django.db.models.fields.URLField')(blank=True, max_length=200, null=True)),
            ('is_beta_tester', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('comment', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(blank=True, default=datetime.datetime.now)),
        ))
        db.send_create_signal('feedbacks', ['Feedback'])

        # Adding M2M table for field feedback_categories on 'Feedback'
        m2m_table_name = db.shorten_name('feedbacks_feedback_feedback_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feedback', models.ForeignKey(orm['feedbacks.feedback'], null=False)),
            ('feedbackcategory', models.ForeignKey(orm['feedbacks.feedbackcategory'], null=False))
        ))
        db.create_unique(m2m_table_name, ['feedback_id', 'feedbackcategory_id'])


    def backwards(self, orm):
        # Deleting model 'FeedbackCategory'
        db.delete_table('feedbacks_feedbackcategory')

        # Deleting model 'IssueType'
        db.delete_table('feedbacks_issuetype')

        # Deleting model 'Feedback'
        db.delete_table('feedbacks_feedback')

        # Removing M2M table for field feedback_categories on 'Feedback'
        db.delete_table(db.shorten_name('feedbacks_feedback_feedback_categories'))


    models = {
        'feedbacks.feedback': {
            'Meta': {'object_name': 'Feedback', 'ordering': "['created']"},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'country': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '100', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'blank': 'True', 'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'blank': 'True', 'max_length': '75', 'null': 'True'}),
            'feedback_categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'null': 'True', 'to': "orm['feedbacks.FeedbackCategory']", 'symmetrical': 'False', 'related_name': "'feedbacks'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_beta_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'issue_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'null': 'True', 'to': "orm['feedbacks.IssueType']", 'related_name': "'feedbacks'"}),
            'name': ('django.db.models.fields.CharField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'}),
            'referral_url': ('django.db.models.fields.URLField', [], {'blank': 'True', 'max_length': '200', 'null': 'True'})
        },
        'feedbacks.feedbackcategory': {
            'Meta': {'object_name': 'FeedbackCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'feedbacks.issuetype': {
            'Meta': {'object_name': 'IssueType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        }
    }

    complete_apps = ['feedbacks']