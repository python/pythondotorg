"""
This module holds models to store generic assets
from Sponsors or Sponsorships
"""
from pathlib import Path

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from polymorphic.models import PolymorphicModel


def generic_asset_path(instance, filename):
    """
    Uses internal name + content type + obj id to avoid name collisions
    """
    directory = "sponsors-assets"
    ext = "".join(Path(filename).suffixes)
    name = f"{instance.internal_name} - {instance.content_type} - {instance.object_id}{ext}"
    return f"{directory}{name}{ext}"


class GenericAsset(PolymorphicModel):
    """
    Base class used to add required assets to Sponsor or Sponsorship objects
    """
    # The next 3 fields are required by Django to enable and set up generic relations
    # pointing the asset to a Sponsor or Sponsorship object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    # must match with internal_name from benefits configuration which describe assets
    internal_name = models.CharField(
        max_length=128,
        verbose_name="Internal Name",
        db_index=True,
    )

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        unique_together = ["content_type", "object_id", "internal_name"]


class ImgAsset(GenericAsset):
    image = models.ImageField(
        upload_to=generic_asset_path,
        blank=False,
        null=True,
    )

    def __str__(self):
        return f"Image asset: {self.internal_name}"

    class Meta:
        verbose_name = "Image Asset"
        verbose_name_plural = "Image Assets"
