import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.urls import reverse
from django.db import models
from django.utils import timezone

from markupfield.fields import MarkupField
from tastypie.models import create_api_key
from rest_framework.authtoken.models import Token

from .managers import UserManager

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'markdown')


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})


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

    objects = CustomUserManager()

    def get_absolute_url(self):
        return reverse('users:user_detail', kwargs={'slug': self.username})

    @property
    def has_membership(self):
        try:
            self.membership
            return True
        except Membership.DoesNotExist:
            return False

    @property
    def sponsorships(self):
        from sponsors.models import Sponsorship
        return Sponsorship.objects.visible_to(self)

    @property
    def api_v2_token(self):
        try:
            return Token.objects.get(user=self).key
        except Token.DoesNotExist:
            return ""


models.signals.post_save.connect(create_api_key, sender=User)


class Membership(models.Model):
    BASIC = 0
    SUPPORTING = 1
    SPONSOR = 2
    CONTRIBUTING = 4
    FELLOW = 5

    MEMBERSHIP_CHOICES = (
        (BASIC, 'Basic Member'),
        (SUPPORTING, 'Supporting Member'),
        (SPONSOR, 'Sponsor Member'),
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
    psf_code_of_conduct = models.BooleanField('I agree to the PSF Code of Conduct', blank=True, null=True)
    psf_announcements = models.BooleanField('I would like to receive occasional PSF email announcements', blank=True, null=True)

    # Voting
    votes = models.BooleanField("I would like to be a PSF Voting Member", default=False)
    last_vote_affirmation = models.DateTimeField(blank=True, null=True)

    created = models.DateTimeField(default=timezone.now, blank=True)
    updated = models.DateTimeField(default=timezone.now, blank=True)

    creator = models.OneToOneField(
        User,
        related_name='membership',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

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


class UserGroup(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    url = models.URLField('URL')

    TYPE_MEETUP = 'meetup'
    TYPE_DISTRIBUTION_LIST = 'distribution list'
    TYPE_OTHER = 'other'

    TYPE_CHOICES = (
        (TYPE_MEETUP, 'Meetup'),
        (TYPE_DISTRIBUTION_LIST, 'Distribution List'),
        (TYPE_OTHER, 'Other'),
    )
    url_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
    )

    start_date = models.DateField(null=True)
    approved = models.BooleanField(default=False)
    trusted = models.BooleanField(default=False)
