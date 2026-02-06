"""Models for Python success stories and their categories."""

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from markupfield.fields import MarkupField

from apps.boxes.models import Box
from apps.cms.models import ContentManageable, NameSlugModel
from apps.companies.models import Company
from apps.successstories.managers import StoryManager
from fastly.utils import purge_url

PSF_TO_EMAILS = ["psf-staff@python.org"]
DEFAULT_MARKUP_TYPE = getattr(settings, "DEFAULT_MARKUP_TYPE", "restructuredtext")


class StoryCategory(NameSlugModel):
    """A category used to classify success stories (e.g. Arts, Business)."""

    class Meta:
        """Meta configuration for StoryCategory."""

        ordering = ("name",)
        verbose_name = "story category"
        verbose_name_plural = "story categories"

    def __str__(self):
        """Return the category name."""
        return self.name

    def get_absolute_url(self):
        """Return the URL for the category's story listing page."""
        return reverse("success_story_list_category", kwargs={"slug": self.slug})


class Story(NameSlugModel, ContentManageable):
    """A Python success story submitted by the community or PSF staff."""

    company_name = models.CharField(max_length=500)
    company_url = models.URLField(verbose_name="Company URL")
    company = models.ForeignKey(
        Company,
        related_name="success_stories",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        StoryCategory,
        related_name="success_stories",
        on_delete=models.CASCADE,
    )
    author = models.CharField(max_length=500, help_text="Author of the content")
    author_email = models.EmailField(max_length=100, blank=True, null=True)  # noqa: DJ001
    pull_quote = models.TextField()
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False, db_index=True)
    featured = models.BooleanField(default=False, help_text="Set to use story in the supernav")
    image = models.ImageField(upload_to="successstories", blank=True, null=True)

    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL)

    objects = StoryManager()

    class Meta:
        """Meta configuration for Story."""

        ordering = ("-created",)
        verbose_name = "story"
        verbose_name_plural = "stories"

    def __str__(self):
        """Return the story name."""
        return self.name

    def get_absolute_url(self):
        """Return the URL for the story detail page."""
        return reverse("success_story_detail", kwargs={"slug": self.slug})

    def get_admin_url(self):
        """Return the Django admin URL for this story."""
        return reverse("admin:successstories_story_change", args=(self.id,))

    def get_company_name(self):
        """Return company name depending on ForeignKey."""
        if self.company:
            return self.company.name
        return self.company_name

    def get_company_url(self):
        """Return the company URL, preferring the linked Company object."""
        if self.company:
            return self.company.url
        return self.company_url


@receiver(post_save, sender=Story)
def update_successstories_supernav(sender, instance, created, **kwargs):
    """Update download supernav."""
    # Skip in fixtures
    if kwargs.get("raw", False):
        return

    if instance.is_published and instance.featured:
        content = render_to_string(
            "successstories/supernav.html",
            {
                "story": instance,
            },
        )

        box, created = Box.objects.update_or_create(
            label="supernav-python-success-stories",
            defaults={
                "content": content,
                "content_markup_type": "html",
            },
        )
        if not created:
            box.save()

        # Purge Fastly cache
        purge_url("/box/supernav-python-success-stories/")

    if instance.is_published:
        # Purge the page itself
        purge_url(instance.get_absolute_url())


@receiver(post_save, sender=Story)
def send_email_to_psf(sender, instance, created, **kwargs):
    """Send a notification email to PSF staff when a new unpublished story is submitted."""
    # Skip in fixtures
    if kwargs.get("raw", False) or not created:
        return

    if not instance.is_published:
        body = """\
Name: {name}
Company name: {company_name}
Company URL: {company_url}
Category: {category}
Author: {author}
Author email: {author_email}
Pull quote:

{pull_quote}

Content:

{content}

Review URL: {admin_url}
        """
        name_lines = instance.name.splitlines()
        name = name_lines[0] if name_lines else instance.name
        email = EmailMessage(
            f"New success story submission: {name}",
            body.format(
                name=instance.name,
                company_name=instance.company_name,
                company_url=instance.company_url,
                category=instance.category.name,
                author=instance.author,
                author_email=instance.author_email,
                pull_quote=instance.pull_quote,
                content=instance.content.raw,
                admin_url=f"https://{Site.objects.get_current()}{instance.get_admin_url()}",
            ).strip(),
            settings.DEFAULT_FROM_EMAIL,
            PSF_TO_EMAILS,
            reply_to=[instance.author_email],
        )
        email.send()
