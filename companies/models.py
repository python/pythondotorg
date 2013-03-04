from django.db import models
from django.utils.translation import ugettext_lazy as _

from cms.models import NameSlugModel


class Company(NameSlugModel):
    about = models.TextField(null=True, blank=True)
    contact = models.CharField(null=True, blank=True, max_length=100)
    email = models.EmailField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    class Meta:
        verbose_name_plural = _("companies")
