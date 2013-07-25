import re
from django.db import models

from cms.models import ContentManageable


class PepType(ContentManageable):
    abbreviation = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'PEP Type'
        verbose_name_plural = 'PEP Types'

    def __str__(self):
        return "{0} ({1})".format(self.name, self.abbreviation)


class PepStatus(ContentManageable):
    abbreviation = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'PEP Status'
        verbose_name_plural = 'PEP Statuses'

    def __str__(self):
        return "{0} ({1})".format(self.name, self.abbreviation)


class PepOwner(ContentManageable):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'PEP Owner'
        verbose_name_plural = 'PEP Owners'

    def __str__(self):
        return "{0} ({1})".format(self.name, self.email)

    def email_display(self):
        return re.sub(r'\@', ' at ', self.email)


class PepCategory(ContentManageable):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'PEP Category'
        verbose_name_plural = 'PEP Categories'

    def __str__(self):
        return self.name


class Pep(ContentManageable):
    type = models.ForeignKey(PepType, related_name='peps')
    status = models.ForeignKey(PepStatus, related_name='peps', blank=True, null=True)
    category = models.ForeignKey(PepCategory, related_name='peps')
    owners = models.ManyToManyField(PepOwner, related_name='peps')
    title = models.CharField(max_length=200)
    number = models.IntegerField()
    url = models.URLField('URL', max_length=255)

    class Meta:
        verbose_name = 'PEP'
        verbose_name_plural = 'PEPs'

    def __str__(self):
        return "PEP {0} '{1}'".format(self.number, self.title)

    def get_owner_names(self):
        names = [x.name for x in self.owners.all()]
        return ",".join(names)

