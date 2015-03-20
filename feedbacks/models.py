from django.db import models
from django.utils import timezone

from cms.models import NameSlugModel


class FeedbackCategory(NameSlugModel):

    class Meta:
        verbose_name = 'feedback category'
        verbose_name_plural = 'feedback categories'


class IssueType(NameSlugModel):

    class Meta:
        verbose_name = 'issue type'
        verbose_name_plural = 'issue types'


class Feedback(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    feedback_categories = models.ManyToManyField(FeedbackCategory, related_name='feedbacks', null=True, blank=True)
    issue_type = models.ForeignKey(IssueType, related_name='feedbacks', null=True, blank=True)
    referral_url = models.URLField(null=True, blank=True)
    is_beta_tester = models.BooleanField(default=False, blank=True)
    comment = models.TextField()
    created = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        ordering = ['created']
        verbose_name = 'feedback'
        verbose_name_plural = 'feedbacks'

    def __str__(self):
        return self.name
