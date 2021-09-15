from django.db import models


class BaseEmailTemplate(models.Model):
    internal_name = models.CharField(max_length=128)

    subject = models.CharField(max_length=128)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
