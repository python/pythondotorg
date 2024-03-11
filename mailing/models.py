from django.core.mail import EmailMessage
from django.db import models
from django.template import Template, Context
from django.urls import reverse


class BaseEmailTemplate(models.Model):
    internal_name = models.CharField(max_length=128)

    subject = models.CharField(max_length=128)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def preview_content_url(self):
        prefix = self._meta.db_table
        url_name = f"admin:{prefix}_preview"
        return reverse(url_name, args=[self.pk])

    def render_content(self, context):
        template = Template(self.content)
        ctx = Context(context)
        return template.render(ctx)

    def render_subject(self, context):
        template = Template(self.subject)
        ctx = Context(context)
        return template.render(ctx)

    def get_email(self, from_email, to, context=None, **kwargs):
        context = context or {}
        context = self.get_email_context_data(**context)
        subject = self.render_subject(context)
        content = self.render_content(context)
        return EmailMessage(subject, content, from_email, to, **kwargs)

    def get_email_context_data(self, **kwargs):
        return kwargs

    class Meta:
        abstract = True

    def __str__(self):
        return f"Email template: {self.internal_name}"
