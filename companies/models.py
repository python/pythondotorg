from django.utils.translation import ugettext_lazy as _

from cms.models import NameSlugModel


class Company(NameSlugModel):
    class Meta:
        verbose_name_plural = _("companies")
