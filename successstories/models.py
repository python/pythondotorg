from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from markupfield.fields import MarkupField

from .managers import StoryManager
from boxes.models import Box
from cms.models import ContentManageable, NameSlugModel
from companies.models import Company


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
    company_url = models.URLField()
    company = models.ForeignKey(Company, blank=True, null=True, related_name='success_stories')
    category = models.ForeignKey(StoryCategory, related_name='success_stories')
    author = models.CharField(max_length=500)
    pull_quote = models.TextField()
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False, db_index=True)
    featured = models.BooleanField(default=False, help_text="Set to use story in the supernav")
    weight = models.IntegerField(
        default=0,
        help_text="Percentage weight given to display, enter 11 for 11% of views. Warnings will be given in flash messages if total of featured Stories is not equal to 100%",
    )
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

    def get_weight_display(self):
        """ Display more useful weight with percent sign in admin """
        return "{} %".format(self.weight)
    get_weight_display.short_description = 'Weight'

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

    def clean(self):
        """ Ensure featured and weight together behave as expected """
        # Doesn't make sense to be featured and never show it
        if self.featured and self.weight == 0:
            raise ValidationError("Cannot be a featured story with weight==0")

        # Can't have a single featured story shown more than 100% of the time
        if self.weight > 100:
            raise ValidationError("weight cannot exceed 100")


@receiver(post_save, sender=Story)
def update_successstories_supernav(sender, instance, signal, created, **kwargs):
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
