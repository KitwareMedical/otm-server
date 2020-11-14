from enum import Enum
from typing import Type

from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from s3_file_field import S3FileField

from .dataset import Dataset
from .patient import Patient


class ImageType(Enum):
    structural_mri = 'structural_mri'


def validate_metadata(val) -> None:
    if not isinstance(val, dict):
        raise ValidationError('Must be a JSON Object.')


class MetadataField(models.JSONField):
    empty_values = [{}]

    def __init__(self, *args, **kwargs):
        kwargs['default'] = dict
        kwargs['blank'] = True
        super().__init__(*args, **kwargs)
        self.validators.append(validate_metadata)


class Image(models.Model):
    class Meta:
        indexes = [models.Index(fields=['dataset'])]
        ordering = ['name']

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100, default=ImageType.structural_mri)
    blob = S3FileField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='images')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='images')
    metadata = MetadataField()

    @property
    def size(self) -> int:
        return self.blob.size


@receiver(models.signals.post_delete, sender=Image)
def _image_delete(sender: Type[Image], instance: Image, *args, **kwargs):
    # TODO delete blob from storage, or write a need-to-delete record to DB
    pass
