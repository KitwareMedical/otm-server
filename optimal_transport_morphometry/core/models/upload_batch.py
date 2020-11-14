from django.db import models

from .dataset import Dataset


class UploadBatch(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='upload_batches')

    @property
    def is_complete(self) -> bool:
        return self.pending_uploads.count() == 0
