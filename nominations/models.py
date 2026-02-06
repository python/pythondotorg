import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from fastly.utils import purge_url
from markupfield.fields import MarkupField

from cms.models import ContentManageable
from users.models import User

from .managers import FellowNominationQuerySet


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

    def get_accept_url(self):
        return reverse(
            "nominations:nomination_accept",
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


class Fellow(models.Model):
    """A PSF Fellow — reference data managed via Django admin."""

    ACTIVE = "active"
    EMERITUS = "emeritus"
    DECEASED = "deceased"
    STATUS_CHOICES = (
        (ACTIVE, "Active"),
        (EMERITUS, "Emeritus"),
        (DECEASED, "Deceased"),
    )

    name = models.CharField(max_length=255)
    year_elected = models.PositiveIntegerField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=ACTIVE,
        db_index=True,
    )
    emeritus_year = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fellow",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FellowNominationRound(models.Model):
    """Quarterly round for PSF Fellow Work Group consideration."""

    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4
    QUARTER_CHOICES = (
        (Q1, "Q1 (Jan-Mar)"),
        (Q2, "Q2 (Apr-Jun)"),
        (Q3, "Q3 (Jul-Sep)"),
        (Q4, "Q4 (Oct-Dec)"),
    )

    year = models.PositiveIntegerField()
    quarter = models.PositiveSmallIntegerField(choices=QUARTER_CHOICES)
    quarter_start = models.DateField(help_text="First day of the quarter.")
    quarter_end = models.DateField(help_text="Last day of the quarter.")
    nominations_cutoff = models.DateField(
        help_text="20th of month 2 per WG Charter (Feb 20, May 20, Aug 20, Nov 20)."
    )
    review_start = models.DateField(help_text="Same as nominations cutoff.")
    review_end = models.DateField(
        help_text="20th of month 3 (Mar 20, Jun 20, Sep 20, Dec 20)."
    )
    is_open = models.BooleanField(default=True, help_text="Whether accepting nominations.")
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        unique_together = ("year", "quarter")
        ordering = ["-year", "-quarter"]

    def __str__(self):
        return f"{self.year} Q{self.quarter}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{self.year}-q{self.quarter}"
        super().save(*args, **kwargs)

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.quarter_start <= today <= self.quarter_end

    @property
    def is_accepting_nominations(self):
        today = timezone.now().date()
        return self.is_open and today <= self.nominations_cutoff

    @property
    def is_in_review(self):
        today = timezone.now().date()
        return self.review_start <= today <= self.review_end


class FellowNomination(ContentManageable):
    """A nomination for the PSF Fellow membership."""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    NOT_ACCEPTED = "not_accepted"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (UNDER_REVIEW, "Under Review"),
        (ACCEPTED, "Accepted"),
        (NOT_ACCEPTED, "Not Accepted"),
    )

    nominee_name = models.CharField(max_length=255)
    nominee_email = models.EmailField(max_length=255)
    nomination_statement = MarkupField(
        escape_html=True, markup_type="markdown"
    )
    nominator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="fellow_nominations_made",
        on_delete=models.CASCADE,
    )
    nomination_round = models.ForeignKey(
        FellowNominationRound,
        related_name="nominations",
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True,
    )
    expiry_round = models.ForeignKey(
        FellowNominationRound,
        related_name="expiring_nominations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Round 4 quarters after submission; nomination expires after this round.",
    )
    nominee_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="fellow_nominations_received",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Linked if nominee has a python.org account.",
    )
    nominee_is_fellow_at_submission = models.BooleanField(
        default=False,
        help_text="Snapshot: was the nominee already a Fellow at submission time?",
    )

    objects = FellowNominationQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Fellow Nomination: {self.nominee_name} (by {self.nominator})"

    def get_absolute_url(self):
        return reverse("nominations:fellow_nomination_detail", kwargs={"pk": self.pk})

    @property
    def is_active(self):
        if self.status in (self.ACCEPTED, self.NOT_ACCEPTED):
            return False
        if self.expiry_round and self.expiry_round.quarter_end < timezone.now().date():
            return False
        return True

    @property
    def nominee_is_already_fellow(self):
        if self.nominee_user:
            try:
                return self.nominee_user.fellow is not None
            except Fellow.DoesNotExist:
                return False
        return False

    @property
    def vote_result(self):
        """Per WG Charter: 50%+1 of votes cast (excluding abstentions)."""
        votes = self.votes.exclude(vote="abstain")
        total = votes.count()
        if total == 0:
            return None
        yes_count = votes.filter(vote="yes").count()
        return yes_count > total / 2


class FellowNominationVote(models.Model):
    """WG member vote on a Fellow nomination."""

    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"
    VOTE_CHOICES = (
        (YES, "Yes"),
        (NO, "No"),
        (ABSTAIN, "Abstain"),
    )

    nomination = models.ForeignKey(
        FellowNomination,
        related_name="votes",
        on_delete=models.CASCADE,
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="fellow_nomination_votes",
        on_delete=models.CASCADE,
    )
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    comment = models.TextField(blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("nomination", "voter")

    def __str__(self):
        return f"{self.voter} voted {self.vote} on {self.nomination}"


@receiver(post_save, sender=FellowNomination)
def purge_fellow_nomination_pages(sender, instance, created, **kwargs):
    """Purge Fastly CDN cache for Fellow nomination pages."""
    if kwargs.get("raw", False):
        return
    purge_url(instance.get_absolute_url())
