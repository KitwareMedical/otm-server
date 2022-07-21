import csv
from typing import TextIO

from django.db import transaction

from optimal_transport_morphometry.core import models


@transaction.atomic
def load_batch_from_csv(csvfile: TextIO, dest: models.Dataset) -> models.UploadBatch:
    reader = csv.DictReader(csvfile)
    batch = models.UploadBatch.objects.create(dataset=dest)
    uploads = []

    for row in reader:
        expected_name = row.pop('name')
        uploads.append(models.PendingUpload(batch=batch, name=expected_name, metadata=row))

    models.PendingUpload.objects.bulk_create(uploads)

    return batch
