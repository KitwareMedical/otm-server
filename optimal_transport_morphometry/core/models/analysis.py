from django.db import models
from django_extensions.db.models import TimeStampedModel
from s3_file_field import S3FileField

from .preprocessing import PreprocessingBatch


class AnalysisResult(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'Pending'
        RUNNING = 'Running'
        FINISHED = 'Finished'
        FAILED = 'Failed'

    # The preprocessed images that this analysis was run on
    preprocessing_batch = models.ForeignKey(
        PreprocessingBatch, related_name='analysis_results', on_delete=models.CASCADE
    )

    # Resulting data
    zip_file = S3FileField(null=True, blank=True, default=None)
    data = models.JSONField(default=dict)

    # Status/Result
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default='')
