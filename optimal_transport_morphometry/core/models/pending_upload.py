from django.db import models

from .patient import Patient
from .upload_batch import UploadBatch


class PendingUpload(models.Model):
    class Meta:
        indexes = [models.Index(fields=['batch', 'name'])]

    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name='pending_uploads')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pending_uploads')
    name = models.CharField(max_length=255)
