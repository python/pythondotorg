from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from markupfield.fields import MarkupField

from .managers import UserManager


DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'markdown')


class User(AbstractUser):
    bio = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE)
    legal_name = models.CharField(max_length=100, blank=True)
    preferred_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField('State, Province or Region', max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # PSF fields
    psf_code_of_conduct = models.NullBooleanField('I agree to the PSF Code of Conduct', blank=True)
    psf_announcements = models.NullBooleanField('I would like to receive occasional PSF email announcements', blank=True)

    SEARCH_PRIVATE = 0
    SEARCH_PUBLIC = 1
    SEARCH_CHOICES = (
        (SEARCH_PUBLIC, 'Allow search engines to index my profile page (recommended)'),
        (SEARCH_PRIVATE, "Don't allow search engines to index my profile page"),
    )
    search_visibility = models.IntegerField(choices=SEARCH_CHOICES, default=SEARCH_PUBLIC)

    EMAIL_PUBLIC = 0
    EMAIL_PRIVATE = 1
    EMAIL_NEVER = 2
    EMAIL_CHOICES = (
        (EMAIL_PUBLIC, 'Anyone can see my e-mail address'),
        (EMAIL_PRIVATE, 'Only logged-in users can see my e-mail address'),
        (EMAIL_NEVER, 'No one can ever see my e-mail address'),
    )
    email_privacy = models.IntegerField('E-mail privacy', choices=EMAIL_CHOICES, default=EMAIL_NEVER)

    objects = UserManager()

    def get_absolute_url(self):
        return reverse('users:user_detail', kwargs={'slug': self.username})
