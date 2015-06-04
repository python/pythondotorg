from django.db import models
from django.conf import settings

from markupfield.fields import MarkupField

from cms.models import ContentManageable, NameSlugModel

DEFAULT_MARKUP_TYPE = getattr(settings, 'DEFAULT_MARKUP_TYPE', 'restructuredtext')


class WorkGroup(ContentManageable, NameSlugModel):
    """
    Model to store Python Working Groups
    """
    active = models.BooleanField(default=True, db_index=True)
    approved = models.BooleanField(default=False, db_index=True)

    short_description = models.TextField(
        blank=True,
        help_text="Short description used on listing pages",
    )

    purpose = MarkupField(
        default_markup_type=DEFAULT_MARKUP_TYPE,
        help_text="State what the mission of the group is. List all (if any) common goals that will be shared amongst the workgroup.",
    )
    active_time = MarkupField(
        default_markup_type=DEFAULT_MARKUP_TYPE,
        help_text="How long will this workgroup exist? If the mission is not complete by the stated time, is it extendable? Is so, for how long?",
    )
    core_values = MarkupField(
        default_markup_type=DEFAULT_MARKUP_TYPE,
        help_text="List the core values that the workgroup will adhere to throughout its existence. Will the workgroup adopt any statements? If so, which statement?",
    )
    rules = MarkupField(
        default_markup_type=DEFAULT_MARKUP_TYPE,
        help_text="Give a comprehensive explanation of how the decision making will work within the workgroup and list the rules that accompany these procedures.",
    )
    communication = MarkupField(
        default_markup_type=DEFAULT_MARKUP_TYPE,
        help_text="How will the team communicate? How often will the team communicate?",
    )
    support = MarkupField(
        blank=True,
        default_markup_type=DEFAULT_MARKUP_TYPE,
        help_text="What resources will you need from the PSF in order to have a functional and effective workgroup?",
    )

    url = models.URLField('URL', blank=True, help_text="Main URL for Group")

    organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="+"
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="working_groups",
    )
