from typing import Type

from django.db import models
from django.dispatch import receiver

from .metadata import MetadataField
from .patient import Patient
from .upload_batch import UploadBatch


class PendingUpload(models.Model):
    class Meta:
        indexes = [models.Index(fields=['batch', 'name'])]
        constraints = [models.UniqueConstraint(fields=['batch', 'name'], name='unique_name')]

    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name='pending_uploads')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pending_uploads')
    name = models.CharField(max_length=255)
    metadata = MetadataField()


@receiver(models.signals.post_delete, sender=PendingUpload)
def _on_delete(sender: Type[PendingUpload], instance: PendingUpload, **kwargs):
    if instance.batch.pending_uploads.count() == 0:
        instance.batch.delete()
