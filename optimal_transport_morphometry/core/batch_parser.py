import csv
from typing import TextIO

from django.db import IntegrityError, transaction

from optimal_transport_morphometry.core import models


@transaction.atomic
def load_batch_from_csv(csvfile: TextIO, dataset: models.Dataset) -> models.UploadBatch:
    reader = csv.DictReader(csvfile)
    batch = models.UploadBatch.objects.create(dataset=dataset)

    # Fetch existing image names
    existing_image_names = set(
        models.Image.objects.filter(dataset=dataset).values_list('name', flat=True)
    )

    # Collect uploads
    uploads = []
    for row in reader:
        expected_name = row.pop('name')
        if expected_name not in existing_image_names:
            uploads.append(models.PendingUpload(batch=batch, name=expected_name, metadata=row))

    # Bulk create pending uploads, ignoring any duplicates
    created = models.PendingUpload.objects.bulk_create(uploads, ignore_conflicts=True)

    # Roll back transaction if none were actually created, so empty batch doesn't still exist
    if not created:
        raise IntegrityError()

    return batch
