from django.db import models


class Banner(models.Model):

    title = models.CharField(
        max_length=1024, help_text="Text to display in the banner's button"
    )
    message = models.CharField(
        max_length=2048, help_text="Message to display in the banner"
    )
    link = models.CharField(max_length=1024, help_text="Link the button will go to")
    active = models.BooleanField(
        null=False, default=False, help_text="Make the banner active on the site"
    )
    psf_pages_only = models.BooleanField(
        null=False, default=True, help_text="Display the banner on /psf pages only"
    )
