import datetime

from django.db import models
from django.utils.text import slugify

from markupfield.fields import MarkupField

from users.models import User


class Election(models.Model):

    def __str__(self):
        return f"{self.name} - {self.date}"

    name = models.CharField(max_length=100)
    date = models.DateField()
    nominations_open = models.DateTimeField(blank=True, null=True)
    nominations_close = models.DateTimeField(blank=True, null=True)

    slug = models.SlugField(max_length=255, blank=True, null=True)

    @property
    def nominations_closed(self):
        if self.nominations_close:
            return datetime.datetime.now(datetime.timezone.utc) > self.nominations_close

        return False

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Election, self).save(*args, **kwargs)


class Nominee(models.Model):

    def __str__(self):
        return f"{self.name}"

    election = models.ForeignKey(
        Election, related_name="nominees", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=1024, blank=False, null=True)
    email = models.CharField(max_length=1024, blank=False, null=True)
    previous_board_service = models.CharField(max_length=1024, blank=False, null=True)
    employer = models.CharField(max_length=1024, blank=False, null=True)
    other_affiliations = models.CharField(max_length=2048, blank=True, null=True)

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

    def editable(self, user=None):
        return user == self.user

    def visible(self, user=None):
        if self.accepted and self.approved and self.election.nominations_closed:
            return True

        if user is None:
            return False

        if user.is_staff or user == self.user:
            return True

        return False

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Nominee, self).save(*args, **kwargs)


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

    def editable(self, user=None):
        if user == self.nominee:
            return True

        if user == self.nominator and not (self.accepted or self.approved):
            return True

        return False

    def visible(self, user=None):
        if self.accepted and self.approved and self.election.nominations_closed:
            return True

        if user is None:
            return False

        if user.is_staff or user == self.nominee or user == self.nominator:
            return True

        return False
