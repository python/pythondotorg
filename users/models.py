import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from markupfield.fields import MarkupField
from tastypie.models import create_api_key

from .managers import UserManager

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'markdown')


class User(AbstractUser):
    bio = MarkupField(blank=True, default_markup_type=DEFAULT_MARKUP_TYPE, escape_html=True)

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

    public_profile = models.BooleanField('Make my profile public', default=True)

    objects = UserManager()

    def get_absolute_url(self):
        return reverse('users:user_detail', kwargs={'slug': self.username})

    @property
    def has_membership(self):
        try:
            self.membership
            return True
        except Membership.DoesNotExist:
            return False

models.signals.post_save.connect(create_api_key, sender=User)


class Membership(models.Model):
    BASIC = 0
    SUPPORTING = 1
    SPONSOR = 2
    MANAGING = 3
    CONTRIBUTING = 4
    FELLOW = 5

    MEMBERSHIP_CHOICES = (
        (BASIC, 'Basic Member'),
        (SUPPORTING, 'Supporting Member'),
        (SPONSOR, 'Sponsor Member'),
        (MANAGING, 'Managing Member'),
        (CONTRIBUTING, 'Contributing Member'),
        (FELLOW, 'Fellow'),
    )

    membership_type = models.IntegerField(default=BASIC, choices=MEMBERSHIP_CHOICES)
    legal_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100)
    email_address = models.EmailField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField('State, Province or Region', max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # PSF fields
    psf_code_of_conduct = models.NullBooleanField('I agree to the PSF Code of Conduct', blank=True)
    psf_announcements = models.NullBooleanField('I would like to receive occasional PSF email announcements', blank=True)

    # Voting
    votes = models.BooleanField("I would like to be a PSF Voting Member", default=False)
    last_vote_affirmation = models.DateTimeField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now, blank=True)
    updated = models.DateTimeField(blank=True)

    creator = models.OneToOneField(User, null=True, blank=True, related_name='membership')

    def __str__(self):
        if self.creator:
            return "Membership for user: %s" % self.creator.username
        else:
            return "Membership '%s'" % self.legal_name

    @property
    def higher_level_member(self):
        if self.membership_type != Membership.BASIC:
            return True
        else:
            return False

    @property
    def needs_vote_affirmation(self):
        if not self.votes:
            return False

        if self.last_vote_affirmation:
            last_year = timezone.now() - datetime.timedelta(days=366)
            if self.last_vote_affirmation < last_year:
                return True

        return False

    def save(self, **kwargs):
        self.updated = timezone.now()

        # Record initial vote affirmation
        if not self.last_vote_affirmation and self.votes:
            self.last_vote_affirmation = timezone.now()

        return super().save(**kwargs)
