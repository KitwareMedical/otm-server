from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

from .atlas import Atlas
from .image import Image


class AbstractPreprocessedImage(TimeStampedModel):
    blob = S3FileField()
    source_image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)ss',
        db_index=True,
    )
    atlas = models.ForeignKey(
        Atlas, on_delete=models.PROTECT, related_name='%(app_label)s_%(class)ss'
    )

    class Meta:
        abstract = True


class FeatureImage(AbstractPreprocessedImage):
    downsample_factor = models.FloatField()


class JacobianImage(AbstractPreprocessedImage):
    pass


class RegisteredImage(AbstractPreprocessedImage):
    registration_type = models.CharField(max_length=100, default='affine')


class SegmentedImage(AbstractPreprocessedImage):
    pass
