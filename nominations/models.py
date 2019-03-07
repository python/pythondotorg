from django.db import models
from django.utils.text import slugify

from markupfield.fields import MarkupField

from users.models import User


class Election(models.Model):
    def __str__(self):
        return f'{self.name} - {self.date}'

    name = models.CharField(max_length=100)
    date = models.DateField()
    nominations_open = models.DateTimeField(blank=True, null=True)
    nominations_close = models.DateTimeField(blank=True, null=True)

    slug = models.SlugField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Election, self).save(*args, **kwargs)


class Nominee(models.Model):
    def __str__(self):
        return f'{self.name}'

    election = models.ForeignKey(Election, related_name="nominees", on_delete=models.CASCADE)
    name = models.CharField(max_length=1024, blank=False, null=True)
    email = models.CharField(max_length=1024, blank=False, null=True)
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

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Nominee, self).save(*args, **kwargs)


class Nomination(models.Model):
    def __str__(self):
        return f'{self.name} <{self.email}>'

    election = models.ForeignKey(Election, on_delete=models.CASCADE)

    name = models.CharField(max_length=1024, blank=False, null=True)
    email = models.CharField(max_length=1024, blank=False, null=True)
    previous_board_service = models.CharField(max_length=1024, blank=False, null=True)
    employer = models.CharField(max_length=1024, blank=False, null=True)
    other_affiliations = models.CharField(max_length=2048, blank=True, null=True)
    nomination_statement = MarkupField(escape_html=True, markup_type='markdown', blank=False, null=True)

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
