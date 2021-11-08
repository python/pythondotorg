"""
This module holds models to store generic assets
from Sponsors or Sponsorships
"""
import uuid
from pathlib import Path

from django import forms
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from polymorphic.models import PolymorphicModel


def generic_asset_path(instance, filename):
    """
    Uses internal name + content type + obj id to avoid name collisions
    """
    directory = "sponsors-app-assets"
    ext = "".join(Path(filename).suffixes)
    name = f"{instance.uuid}"
    return f"{directory}/{name}{ext}"


class GenericAsset(PolymorphicModel):
    """
    Base class used to add required assets to Sponsor or Sponsorship objects
    """
    # UUID can't be the object ID because Polymorphic expects default django integer ID
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
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

    @property
    def value(self):
        return None


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

    @property
    def value(self):
        return self.image


class TextAsset(GenericAsset):
    text = models.TextField(default="")

    def __str__(self):
        return f"Text asset: {self.internal_name}"

    class Meta:
        verbose_name = "Text Asset"
        verbose_name_plural = "Text Assets"

    @property
    def value(self):
        return self.text
