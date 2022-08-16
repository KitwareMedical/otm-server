from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

from .atlas import Atlas
from .dataset import Dataset
from .image import Image


class PreprocessingBatch(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'Pending'
        RUNNING = 'Running'
        FINISHED = 'Finished'
        FAILED = 'Failed'

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name='preprocessing_batches'
    )
    error_message = models.TextField(blank=True, default='')


class AbstractPreprocessedImage(TimeStampedModel):
    """Base class that preprocessed images inherit from."""

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

    # The preprocessing batch this preprocessed image belongs to
    preprocessing_batch = models.ForeignKey(
        PreprocessingBatch,
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s',
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
