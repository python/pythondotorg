"""
This module holds models to store generic assets
from Sponsors or Sponsorships
"""
import uuid
from enum import Enum
from pathlib import Path

from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.files import ImageFieldFile, FileField
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel

from sponsors.models.managers import GenericAssetQuerySet


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
    objects = GenericAssetQuerySet.as_manager()
    non_polymorphic = models.Manager()

    # UUID can't be the object ID because Polymorphic expects default django integer ID
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    # The next 3 fields are required by Django to enable and set up generic relations
    # pointing the asset to a Sponsor or Sponsorship object
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

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
        base_manager_name = 'non_polymorphic'

    @property
    def value(self):
        return None

    @property
    def is_file(self):
        return isinstance(self.value, FileField) or isinstance(self.value, ImageFieldFile)

    @property
    def from_sponsorship(self):
        return self.content_type.name == "sponsorship"

    @property
    def from_sponsor(self):
        return self.content_type.name == "sponsor"

    @property
    def has_value(self):
        if self.is_file:
            return self.value and getattr(self.value, "url", None)
        else:
            return bool(self.value)

    @classmethod
    def all_asset_types(cls):
        return cls.__subclasses__()


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

    @value.setter
    def value(self, value):
        self.image = value


class TextAsset(GenericAsset):
    text = models.TextField(default="", blank=True)

    def __str__(self):
        return f"Text asset: {self.internal_name}"

    class Meta:
        verbose_name = "Text Asset"
        verbose_name_plural = "Text Assets"

    @property
    def value(self):
        return self.text

    @value.setter
    def value(self, value):
        self.text = value


class FileAsset(GenericAsset):
    file = models.FileField(
        upload_to=generic_asset_path,
        blank=False,
        null=True,
    )

    def __str__(self):
        return f"File asset: {self.internal_name}"

    class Meta:
        verbose_name = "File Asset"
        verbose_name_plural = "File Assets"

    @property
    def value(self):
        return self.file

    @value.setter
    def value(self, value):
        self.file = value


class Response(Enum):
    YES = "Yes"
    NO = "No"

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class ResponseAsset(GenericAsset):
    response = models.CharField(
        max_length=32, choices=Response.choices(), blank=False, null=True
    )

    def __str__(self):
        return f"Response Asset: {self.internal_name}"

    class Meta:
        verbose_name = "Response Asset"
        verbose_name_plural = "Response Assets"

    @property
    def value(self):
        return self.response

    @value.setter
    def value(self, value):
        self.response = value
