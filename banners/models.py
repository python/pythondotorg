from django.db import models


class Banner(models.Model):

    title = models.CharField(max_length=1024)
    message = models.CharField(max_length=2048)
    link = models.CharField(max_length=1024)
    active = models.BooleanField(null=False, default=False)
    psf_pages_only = models.BooleanField(null=False, default=True)
