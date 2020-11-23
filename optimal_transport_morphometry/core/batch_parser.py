import csv
from typing import TextIO
from uuid import uuid4

from django.db import transaction

from optimal_transport_morphometry.core import models


@transaction.atomic
def load_batch_from_csv(csvfile: TextIO, dest: models.Dataset) -> models.UploadBatch:
    reader = csv.DictReader(csvfile)
    batch = models.UploadBatch.objects.create(dataset=dest)
    patients = []
    uploads = []

    for row in reader:
        expected_name = row.pop('name')
        patient_id = row.pop('patient', '').strip() or uuid4().hex
        # TODO allow using existing patients too
        patient = models.Patient(identifier=patient_id)
        patients.append(patient)
        uploads.append(
            models.PendingUpload(batch=batch, patient=patient, name=expected_name, metadata=row)
        )

    models.Patient.objects.bulk_create(patients)
    models.PendingUpload.objects.bulk_create(uploads)

    return batch
