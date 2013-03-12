# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Feedback.is_beta_tester'
        db.add_column('feedbacks_feedback', 'is_beta_tester',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Feedback.is_beta_tester'
        db.delete_column('feedbacks_feedback', 'is_beta_tester')


    models = {
        'feedbacks.feedback': {
            'Meta': {'object_name': 'Feedback', 'ordering': "['created']"},
            'comment': ('django.db.models.fields.TextField', [], {}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'feedback_categories': ('django.db.models.fields.related.ManyToManyField', [], {'null': 'True', 'related_name': "'feedbacks'", 'blank': 'True', 'symmetrical': 'False', 'to': "orm['feedbacks.FeedbackCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_beta_tester': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'issue_type': ('django.db.models.fields.related.ForeignKey', [], {'null': 'True', 'related_name': "'feedbacks'", 'blank': 'True', 'to': "orm['feedbacks.IssueType']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'referral_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
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