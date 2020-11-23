from django.db import models
from django_extensions.db.models import CreationDateTimeField

from .dataset import Dataset


class UploadBatch(models.Model):
    class Meta:
        verbose_name = 'upload batch'
        verbose_name_plural = 'upload batches'

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='upload_batches')
    created = CreationDateTimeField()

    @property
    def is_complete(self) -> bool:
        return self.pending_uploads.count() == 0
