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

    class Meta:
        abstract = True
