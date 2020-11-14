from django.db import models
from s3_file_field import S3FileField

from .atlas import Atlas
from .image import Image


class RegisteredImage(models.Model):
    class Meta:
        indexes = models.Index(['batch', 'name'])

    blob = S3FileField()
    source_image = models.ForeignKey(
        Image, on_delete=models.CASCADE, related_name='registered_images'
    )
    atlas = models.ForeignKey(Atlas, on_delete=models.PROTECT, related_name='registered_images')
    registration_type = models.CharField(max_length=100, default='affine')
