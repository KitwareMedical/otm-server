import csv
from typing import TextIO
from uuid import uuid4

from django.db import transaction

from optimal_transport_morphometry.core import models


@transaction.atomic
def load_batch_from_csv(csvfile: TextIO, dest: models.Dataset) -> models.UploadBatch:
    reader = csv.DictReader(csvfile)
    batch = models.UploadBatch.objects.create(dataset=dest)

    for row in reader:
        expected_name = row.pop('name')
        patient_id = row.pop('patient', '').strip() or uuid4().hex
        # TODO allow using existing patients too
        patient = models.Patient.objects.create(identifier=patient_id, metadata=row)
        models.PendingUpload.objects.create(batch=batch, patient=patient, name=expected_name)

    return batch
