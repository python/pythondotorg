"""Models for PSF board elections, nominees, and nominations."""

import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from markupfield.fields import MarkupField

from fastly.utils import purge_url
from users.models import User


class Election(models.Model):
    """A PSF board election with nomination open/close dates."""

    name = models.CharField(max_length=100)
    date = models.DateField()
    nominations_open_at = models.DateTimeField(blank=True, null=True)
    nominations_close_at = models.DateTimeField(blank=True, null=True)
    description = MarkupField(escape_html=False, markup_type="markdown", blank=False, null=True)

    slug = models.SlugField(max_length=255, blank=True)

    class Meta:
        """Meta configuration for Election."""

        ordering = ["-date"]

    def __str__(self):
        """Return election name and date."""
        return f"{self.name} - {self.date}"

    def save(self, *args, **kwargs):
        """Generate slug from name before saving."""
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def nominations_open(self):
        """Return True if the current time is within the nomination window."""
        if self.nominations_open_at and self.nominations_close_at:
            return self.nominations_open_at < datetime.datetime.now(datetime.UTC) < self.nominations_close_at

        return False

    @property
    def nominations_complete(self):
        """Return True if the nomination window has closed."""
        if self.nominations_close_at:
            return self.nominations_close_at < datetime.datetime.now(datetime.UTC)

        return False

    @property
    def status(self):
        """Return human-readable nomination status string."""
        if self.nominations_open_at is not None and self.nominations_close_at is not None:
            if not self.nominations_open:
                if self.nominations_open_at > datetime.datetime.now(datetime.UTC):
                    return "Nominations Not Yet Open"

                return "Nominations Closed"

            return "Nominations Open"
        if self.date >= timezone.now().date():
            return "Commenced"
        return "Voting Not Yet Begun"


class Nominee(models.Model):
    """A user nominated as a candidate in a PSF board election."""

    election = models.ForeignKey(Election, related_name="nominees", on_delete=models.CASCADE)
    user = models.ForeignKey(
        User,
        related_name="nominations_recieved",
        null=True,
        on_delete=models.CASCADE,
        blank=True,
    )

    accepted = models.BooleanField(null=False, default=False)
    approved = models.BooleanField(null=False, default=False)

    slug = models.SlugField(max_length=255, blank=True)

    class Meta:
        """Meta configuration for Nominee."""

        unique_together = ("user", "election")

    def __str__(self):
        """Return the nominee's full name."""
        return f"{self.name}"

    def save(self, *args, **kwargs):
        """Generate slug from name before saving."""
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Return the URL for the nominee detail page."""
        return reverse(
            "nominations:nominee_detail",
            kwargs={"election": self.election.slug, "slug": self.slug},
        )

    @property
    def name(self):
        """Return the nominee's first and last name."""
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def nominations_received(self):
        """Return accepted and approved nominations excluding self-nominations."""
        return self.nominations.filter(accepted=True, approved=True).exclude(nominator=self.user).all()

    @property
    def nominations_pending(self):
        """Return pending nominations excluding self-nominations."""
        return self.nominations.exclude(accepted=False, approved=False).exclude(nominator=self.user).all()

    @property
    def self_nomination(self):
        """Return the self-nomination for this nominee, if any."""
        return self.nominations.filter(nominator=self.user).first()

    @property
    def display_name(self):
        """Return the display name for the nominee."""
        return self.name

    @property
    def display_previous_board_service(self):
        """Return previous board service info, preferring self-nomination data."""
        if self.self_nomination is not None and self.self_nomination.previous_board_service:
            return self.self_nomination.previous_board_service

        return self.nominations.first().previous_board_service

    @property
    def display_employer(self):
        """Return employer info, preferring self-nomination data."""
        if self.self_nomination is not None and self.self_nomination.employer:
            return self.self_nomination.employer

        return self.nominations.first().employer

    @property
    def display_other_affiliations(self):
        """Return other affiliations, preferring self-nomination data."""
        if self.self_nomination is not None and self.self_nomination.other_affiliations:
            return self.self_nomination.other_affiliations

        return self.nominations.first().other_affiliations

    def visible(self, user=None):
        """Return True if the nominee is visible to the given user."""
        if self.accepted and self.approved and not self.election.nominations_open:
            return True

        if user is None:
            return False

        return bool(user.is_staff or user == self.user)


class Nomination(models.Model):
    """A nomination submitted for a candidate in a board election."""

    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    name = models.CharField(max_length=1024, blank=False)
    email = models.CharField(max_length=1024, blank=False)
    previous_board_service = models.CharField(max_length=1024, blank=False)
    employer = models.CharField(max_length=1024, blank=False)
    other_affiliations = models.CharField(max_length=2048, blank=True)
    nomination_statement = MarkupField(escape_html=True, markup_type="markdown", blank=False, null=True)

    nominator = models.ForeignKey(User, related_name="nominations_made", on_delete=models.CASCADE)
    nominee = models.ForeignKey(
        Nominee,
        related_name="nominations",
        null=True,
        on_delete=models.CASCADE,
        blank=True,
    )

    accepted = models.BooleanField(null=False, default=False)
    approved = models.BooleanField(null=False, default=False)

    def __str__(self):
        """Return the nominee name and email."""
        return f"{self.name} <{self.email}>"

    def get_absolute_url(self):
        """Return the URL for the nomination detail page."""
        return reverse(
            "nominations:nomination_detail",
            kwargs={"election": self.election.slug, "pk": self.pk},
        )

    def get_edit_url(self):
        """Return the URL for editing this nomination."""
        return reverse(
            "nominations:nomination_edit",
            kwargs={"election": self.election.slug, "pk": self.pk},
        )

    def get_accept_url(self):
        """Return the URL for accepting this nomination."""
        return reverse(
            "nominations:nomination_accept",
            kwargs={"election": self.election.slug, "pk": self.pk},
        )

    def editable(self, user=None):
        """Return True if the given user can edit this nomination."""
        if self.nominee and user == self.nominee.user and self.election.nominations_open:
            return True

        return bool(user == self.nominator and not (self.accepted or self.approved) and self.election.nominations_open)

    def visible(self, user=None):
        """Return True if the nomination is visible to the given user."""
        if self.accepted and self.approved and not self.election.nominations_open_at:
            return True

        if user is None:
            return False

        if user.is_staff:
            return True

        if user == self.nominator:
            return True

        return bool(self.nominee and user == self.nominee.user)


@receiver(post_save, sender=Nomination)
def purge_nomination_pages(sender, instance, created, **kwargs):
    """Purge pages that contain the rendered markup."""
    # Skip in fixtures
    if kwargs.get("raw", False):
        return

    # Purge the nomination page itself
    purge_url(instance.get_absolute_url())

    if instance.nominee:
        # Purge the nominee page
        purge_url(instance.nominee.get_absolute_url())

    if instance.election:
        # Purge the election page
        purge_url(reverse("nominations:nominees_list", kwargs={"election": instance.election.slug}))
