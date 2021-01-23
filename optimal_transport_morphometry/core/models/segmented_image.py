from django.db import models
from s3_file_field import S3FileField

from .atlas import Atlas
from .image import Image


class SegmentedImage(models.Model):
    blob = S3FileField()
    source_image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='segmented_images',
        db_index=True,
    )
    atlas = models.ForeignKey(Atlas, on_delete=models.PROTECT, related_name='segmented_images')
