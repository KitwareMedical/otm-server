from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

from .atlas import Atlas
from .image import Image


class FeatureImage(TimeStampedModel):
    blob = S3FileField()
    source_image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='feature_images',
        db_index=True,
    )
    atlas = models.ForeignKey(Atlas, on_delete=models.PROTECT, related_name='feature_images')
    downsample_factor = models.FloatField()
