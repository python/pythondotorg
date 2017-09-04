from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.urls import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from markupfield.fields import MarkupField

from .managers import StoryManager
from boxes.models import Box
from cms.models import ContentManageable, NameSlugModel
from companies.models import Company
from fastly.utils import purge_url


PSF_TO_EMAILS = ['ewa@python.org']
DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class StoryCategory(NameSlugModel):

    class Meta:
        ordering = ('name',)
        verbose_name = 'story category'
        verbose_name_plural = 'story categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('success_story_list_category', kwargs={'slug': self.slug})


class Story(NameSlugModel, ContentManageable):
    company_name = models.CharField(max_length=500)
    company_url = models.URLField(verbose_name='Company URL')
    company = models.ForeignKey(
        Company,
        related_name='success_stories',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    category = models.ForeignKey(
        StoryCategory,
        related_name='success_stories',
        on_delete=models.CASCADE,
    )
    author = models.CharField(max_length=500, help_text='Author of the content')
    author_email = models.EmailField(max_length=100, blank=True, null=True)
    pull_quote = models.TextField()
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False, db_index=True)
    featured = models.BooleanField(default=False, help_text="Set to use story in the supernav")
    image = models.ImageField(upload_to='successstories', blank=True, null=True)

    objects = StoryManager()

    class Meta:
        ordering = ('-created',)
        verbose_name = 'story'
        verbose_name_plural = 'stories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('success_story_detail', kwargs={'slug': self.slug})

    def get_admin_url(self):
        return reverse('admin:successstories_story_change', args=(self.id,))

    def get_company_name(self):
        """ Return company name depending on ForeignKey """
        if self.company:
            return self.company.name
        else:
            return self.company_name

    def get_company_url(self):
        if self.company:
            return self.company.url
        else:
            return self.company_url


@receiver(post_save, sender=Story)
def update_successstories_supernav(sender, instance, created, **kwargs):
    """ Update download supernav """
    # Skip in fixtures
    if kwargs.get('raw', False):
        return

    if instance.is_published and instance.featured:
        content = render_to_string('successstories/supernav.html', {
            'story': instance,
        })

        box, _ = Box.objects.get_or_create(label='supernav-python-success-stories')
        box.content = content
        box.save()

        # Purge Fastly cache
        purge_url('/box/supernav-python-success-stories/')

    if instance.is_published:
        # Purge the page itself
        purge_url(instance.get_absolute_url())


@receiver(post_save, sender=Story)
def send_email_to_psf(sender, instance, created, **kwargs):
    # Skip in fixtures
    if kwargs.get('raw', False) or not created:
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
        email = EmailMessage(
            'New success story submission: {}'.format(instance.name),
            body.format(
                name=instance.name,
                company_name=instance.company_name,
                company_url=instance.company_url,
                category=instance.category.name,
                author=instance.author,
                author_email=instance.author_email,
                pull_quote=instance.pull_quote,
                content=instance.content.raw,
                admin_url='https://www.{}{}'.format(
                    Site.objects.get_current(), instance.get_admin_url()
                ),
            ).strip(),
            settings.DEFAULT_FROM_EMAIL,
            PSF_TO_EMAILS,
            reply_to=[instance.author_email],
        )
        email.send()
