"""Abstract base model for Django template-based email templates."""

from django.core.mail import EmailMessage
from django.db import models
from django.template import Context, Engine
from django.urls import reverse


class BaseEmailTemplate(models.Model):
    """Abstract model for storing and rendering email templates using the Django template engine."""

    internal_name = models.CharField(max_length=128)

    subject = models.CharField(max_length=128)
    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta configuration for BaseEmailTemplate."""

        abstract = True

    def __str__(self):
        """Return string representation with the template's internal name."""
        return f"Email template: {self.internal_name}"

    @property
    def preview_content_url(self):
        """Return the admin URL for previewing the rendered template content."""
        prefix = self._meta.db_table
        url_name = f"admin:{prefix}_preview"
        return reverse(url_name, args=[self.pk])

    template_engine = Engine(
        builtins=["django.template.defaultfilters"],
        autoescape=True,
    )

    def render_content(self, context):
        """Render the email body using a sandboxed Django template engine."""
        template = self.template_engine.from_string(self.content)
        ctx = Context(context)
        return template.render(ctx)

    def render_subject(self, context):
        """Render the email subject using a sandboxed Django template engine."""
        template = self.template_engine.from_string(self.subject)
        ctx = Context(context)
        return template.render(ctx)

    def get_email(self, from_email, to, context=None, **kwargs):
        """Build and return an EmailMessage with rendered subject and content."""
        context = context or {}
        context = self.get_email_context_data(**context)
        subject = self.render_subject(context)
        content = self.render_content(context)
        return EmailMessage(subject, content, from_email, to, **kwargs)

    def get_email_context_data(self, **kwargs):
        """Return the context dictionary for template rendering."""
        return kwargs
