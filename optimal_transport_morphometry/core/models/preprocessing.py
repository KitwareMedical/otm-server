from typing import Optional

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

    # The total number of preprocessed images that should be expected in this batch
    # expected_total = models.PositiveIntegerField()

    def source_images(self) -> models.QuerySet[Image]:
        """Return all images that are sources to preprocessed images in this batch."""
        return Image.objects.filter(
            models.Q(core_featureimages__preprocessing_batch=self)
            | models.Q(core_registeredimages__preprocessing_batch=self)
            | models.Q(core_segmentedimages__preprocessing_batch=self)
            | models.Q(core_jacobianimages__preprocessing_batch=self)
        ).distinct()

    def current_image(self) -> Optional[Image]:
        """Return the source image currently being processed, or None."""
        return (
            self.dataset.images.order_by('name')
            .exclude(
                models.Q(
                    name__in=self.core_featureimage.values_list('source_image__name', flat=True)
                )
                & models.Q(
                    name__in=self.core_jacobianimage.values_list('source_image__name', flat=True)
                )
                & models.Q(
                    name__in=self.core_registeredimage.values_list('source_image__name', flat=True)
                )
                & models.Q(
                    name__in=self.core_segmentedimage.values_list('source_image__name', flat=True)
                )
            )
            .first()
        )

    # def save(self, **kwargs):
    #     if not self.expected_total:
    #         self.expected_total = self.dataset.images * 4

    #     return super().save(**kwargs)


class PreprocessedImageType(models.TextChoices):
    FEATURE = 'Feature'
    JACOBIAN = 'Jacobian'
    REGISTERED = 'Registered'
    SEGMENTED = 'Segmented'


class PreprocessedImage(TimeStampedModel):
    """Base class that preprocessed images inherit from."""

    ImageType = PreprocessedImageType

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    ~models.Q(image_type=PreprocessedImageType.FEATURE)
                    | models.Q(metadata__downsample_factor__isnull=False)
                ),
                name='feature_image_required_downsample_factor',
            ),
            models.CheckConstraint(
                check=(
                    ~models.Q(image_type=PreprocessedImageType.REGISTERED)
                    | models.Q(metadata__registration_type__isnull=False)
                ),
                name='registered_image_required_registration_type',
            ),
        ]

    # To keep track of data specific to any image type
    metadata = models.JSONField()

    blob = S3FileField()
    image_type = models.CharField(max_length=32, choices=ImageType.choices)
    atlas = models.ForeignKey(Atlas, on_delete=models.PROTECT, related_name='preprocessed_images')
    source_image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='preprocessed_images',
        db_index=True,
    )

    # The preprocessing batch this preprocessed image belongs to
    preprocessing_batch = models.ForeignKey(
        PreprocessingBatch,
        on_delete=models.CASCADE,
        related_name='preprocessed_images',
    )

    def save(self, **kwargs):
        """Override save to ensure metadata is set."""
        if self.image_type == PreprocessedImageType.FEATURE:
            self.metadata.setdefault('downsample_factor', 3)

        if self.image_type == PreprocessedImageType.REGISTERED:
            self.metadata.setdefault('registration_type', 'affine')

        return super().save(**kwargs)
