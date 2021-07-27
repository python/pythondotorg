import datetime

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify

from fastly.utils import purge_url
from markupfield.fields import MarkupField

from users.models import User


class Election(models.Model):
    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.name} - {self.date}"

    name = models.CharField(max_length=100)
    date = models.DateField()
    nominations_open_at = models.DateTimeField(blank=True, null=True)
    nominations_close_at = models.DateTimeField(blank=True, null=True)
    description = MarkupField(
        escape_html=False, markup_type="markdown", blank=False, null=True
    )

    slug = models.SlugField(max_length=255, blank=True, null=True)

    @property
    def nominations_open(self):
        if self.nominations_open_at and self.nominations_close_at:
            return (
                self.nominations_open_at
                < datetime.datetime.now(datetime.timezone.utc)
                < self.nominations_close_at
            )

        return False

    @property
    def nominations_complete(self):
        if self.nominations_close_at:
            return self.nominations_close_at < datetime.datetime.now(
                datetime.timezone.utc
            )

        return False

    @property
    def status(self):
        if self.nominations_open_at is not None and self.nominations_close_at is not None:
            if not self.nominations_open:
                if self.nominations_open_at > datetime.datetime.now(datetime.timezone.utc):
                    return "Nominations Not Yet Open"

                return "Nominations Closed"

            return "Nominations Open"
        else:
            if self.date >= datetime.date.today():
                return "Commenced"
            return "Voting Not Yet Begun"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Nominee(models.Model):
    class Meta:
        unique_together = ("user", "election")

    def __str__(self):
        return f"{self.name}"

    election = models.ForeignKey(
        Election, related_name="nominees", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name="nominations_recieved",
        null=True,
        on_delete=models.CASCADE,
        blank=True,
    )

    accepted = models.BooleanField(null=False, default=False)
    approved = models.BooleanField(null=False, default=False)

    slug = models.SlugField(max_length=255, blank=True, null=True)

    def get_absolute_url(self):
        return reverse(
            "nominations:nominee_detail",
            kwargs={"election": self.election.slug, "slug": self.slug},
        )

    @property
    def name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def nominations_received(self):
        return (
            self.nominations.filter(accepted=True, approved=True)
            .exclude(nominator=self.user)
            .all()
        )

    @property
    def nominations_pending(self):
        return (
            self.nominations.exclude(accepted=False, approved=False)
            .exclude(nominator=self.user)
            .all()
        )

    @property
    def self_nomination(self):
        return self.nominations.filter(nominator=self.user).first()

    @property
    def display_name(self):
        return self.name

    @property
    def display_previous_board_service(self):
        if (
            self.self_nomination is not None
            and self.self_nomination.previous_board_service
        ):
            return self.self_nomination.previous_board_service

        return self.nominations.first().previous_board_service

    @property
    def display_employer(self):
        if self.self_nomination is not None and self.self_nomination.employer:
            return self.self_nomination.employer

        return self.nominations.first().employer

    @property
    def display_other_affiliations(self):
        if self.self_nomination is not None and self.self_nomination.other_affiliations:
            return self.self_nomination.other_affiliations

        return self.nominations.first().other_affiliations

    def visible(self, user=None):
        if self.accepted and self.approved and not self.election.nominations_open:
            return True

        if user is None:
            return False

        if user.is_staff or user == self.user:
            return True

        return False

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Nomination(models.Model):
    def __str__(self):
        return f"{self.name} <{self.email}>"

    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    name = models.CharField(max_length=1024, blank=False, null=True)
    email = models.CharField(max_length=1024, blank=False, null=True)
    previous_board_service = models.CharField(max_length=1024, blank=False, null=True)
    employer = models.CharField(max_length=1024, blank=False, null=True)
    other_affiliations = models.CharField(max_length=2048, blank=True, null=True)
    nomination_statement = MarkupField(
        escape_html=True, markup_type="markdown", blank=False, null=True
    )

    nominator = models.ForeignKey(
        User, related_name="nominations_made", on_delete=models.CASCADE
    )
    nominee = models.ForeignKey(
        Nominee,
        related_name="nominations",
        null=True,
        on_delete=models.CASCADE,
        blank=True,
    )

    accepted = models.BooleanField(null=False, default=False)
    approved = models.BooleanField(null=False, default=False)

    def get_absolute_url(self):
        return reverse(
            "nominations:nomination_detail",
            kwargs={"election": self.election.slug, "pk": self.pk},
        )

    def get_edit_url(self):
        return reverse(
            "nominations:nomination_edit",
            kwargs={"election": self.election.slug, "pk": self.pk},
        )

    def editable(self, user=None):
        if (
            self.nominee
            and user == self.nominee.user
            and self.election.nominations_open
        ):
            return True

        if (
            user == self.nominator
            and not (self.accepted or self.approved)
            and self.election.nominations_open
        ):
            return True

        return False

    def visible(self, user=None):
        if self.accepted and self.approved and not self.election.nominations_open_at:
            return True

        if user is None:
            return False

        if user.is_staff:
            return True

        if user == self.nominator:
            return True

        if self.nominee and user == self.nominee.user:
            return True

        return False


@receiver(post_save, sender=Nomination)
def purge_nomination_pages(sender, instance, created, **kwargs):
    """ Purge pages that contain the rendered markup """
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
        purge_url(
            reverse(
                "nominations:nominees_list", kwargs={"election": instance.election.slug}
            )
        )
