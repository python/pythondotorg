from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from markupfield.fields import MarkupField

from .managers import StoryManager
from cms.models import ContentManageable, NameSlugModel


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
    category = models.ForeignKey(StoryCategory)
    author = models.CharField(max_length=500)
    pull_quote = models.TextField()
    content = MarkupField(default_markup_type=DEFAULT_MARKUP_TYPE)
    is_published = models.BooleanField(default=False)

    objects = StoryManager()

    class Meta:
        verbose_name = 'story'
        verbose_name_plural = 'stories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('success_story_detail', kwargs={'slug': self.slug})
